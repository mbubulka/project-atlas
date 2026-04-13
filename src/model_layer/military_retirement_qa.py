"""
Military Retirement Q&A Module for ProjectAtlas

This module integrates the Hybrid RAG pipeline for military retirement inquiries.
It provides evidence-based guidance using authenticated Q&A pairs and semantic search.

Architecture:
- FAISS Vector Store: Initial semantic retrieval
- Cross-Encoder: Re-ranking for precision
- FLAN-T5-Base: Abstract answer generation
"""

import json
import os
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from sentence_transformers import SentenceTransformer, CrossEncoder
except ImportError:
    raise ImportError(
        "Required packages not installed. Install with: "
        "pip install torch transformers sentence-transformers"
    )

logger = logging.getLogger(__name__)


class MilitaryRetirementQATool:
    """
    Hybrid RAG pipeline for military retirement Q&A.
    
    Combines retrieval, re-ranking, and generation for accurate,
    evidence-based answers grounded in authenticated Q&A pairs.
    """
    
    def __init__(
        self,
        knowledge_base: List[Dict],
        embedder_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        cross_encoder_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        generator_name: str = "google/flan-t5-base",
        device: str = "cpu"
    ):
        """
        Initialize the Military Retirement QA Tool.
        
        Args:
            knowledge_base: List of dicts with 'question' and 'answer' keys
            embedder_name: Hugging Face model ID for embeddings
            cross_encoder_name: Hugging Face model ID for re-ranking
            generator_name: Hugging Face model ID for generation
            device: 'cpu' or 'cuda'
        """
        self.knowledge_base = knowledge_base
        self.device = torch.device(device)
        
        logger.info(f"Loading embedder: {embedder_name}")
        self.embedder = SentenceTransformer(embedder_name)
        self.embedder.to(self.device)
        
        logger.info(f"Loading cross-encoder: {cross_encoder_name}")
        self.cross_encoder = CrossEncoder(cross_encoder_name)
        self.cross_encoder.to(self.device)
        
        logger.info(f"Loading generator: {generator_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(generator_name)
        self.generator_model = AutoModelForSeq2SeqLM.from_pretrained(generator_name)
        self.generator_model.to(self.device)
        self.generator_model.eval()
        
        # Encode knowledge base for FAISS search
        logger.info("Encoding knowledge base for semantic search...")
        self.kb_embeddings = self._encode_knowledge_base()
        
    def _encode_knowledge_base(self) -> np.ndarray:
        """Encode knowledge base Q&A pairs."""
        texts = [
            f"Q: {item['question']}\nA: {item['answer']}"
            for item in self.knowledge_base
        ]
        embeddings = self.embedder.encode(texts, convert_to_numpy=True)
        return embeddings
    
    def ask(
        self,
        query: str,
        retrieve_k: int = 10,
        final_k: int = 3,
        max_length: int = 256,
        confidence_threshold: float = 0.3
    ) -> Dict[str, any]:
        """
        Answer a military retirement question.
        
        Args:
            query: User's question
            retrieve_k: Initial retrieval pool size
            final_k: Final context passages to use
            max_length: Max generation length
            confidence_threshold: Min cross-encoder score to consider
        
        Returns:
            Dict with 'answer', 'context', 'confidence', 'sources'
        """
        # Encode query
        query_embedding = self.embedder.encode([query], convert_to_numpy=True)[0]
        
        # Retrieve candidates using cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(
            query_embedding.reshape(1, -1),
            self.kb_embeddings
        )[0]
        
        top_indices = np.argsort(similarities)[::-1][:retrieve_k]
        candidates = []
        
        for idx in top_indices:
            if idx < len(self.knowledge_base):
                candidates.append({
                    'index': int(idx),
                    'question': self.knowledge_base[idx]['question'],
                    'answer': self.knowledge_base[idx]['answer'],
                    'retrieval_score': float(similarities[idx]),
                    'text': f"Q: {self.knowledge_base[idx]['question']}\nA: {self.knowledge_base[idx]['answer']}"
                })
        
        if not candidates:
            return {
                'answer': "I'm unable to find relevant information to answer your question. Please consult official DoD resources.",
                'context': [],
                'confidence': 0.0,
                'sources': []
            }
        
        # Re-rank with cross-encoder
        pairs = [[query, cand['text']] for cand in candidates]
        cross_encoder_scores = self.cross_encoder.predict(pairs)
        
        # Sort by cross-encoder score
        for i, cand in enumerate(candidates):
            cand['reranking_score'] = float(cross_encoder_scores[i])
        
        ranked_candidates = sorted(
            candidates,
            key=lambda x: x['reranking_score'],
            reverse=True
        )
        
        # Filter and select top candidates
        selected = [
            c for c in ranked_candidates[:final_k]
            if c['reranking_score'] >= confidence_threshold
        ]
        
        if not selected:
            selected = ranked_candidates[:final_k]
        
        # Construct context
        context_text = ""
        for cand in selected:
            context_text += f"{cand['text']}\n\n"
        
        # Generate answer
        prompt = f"""You are a military retirement advisor. Use the following context to answer the user's question accurately.

Context:
{context_text}

Question: {query}
Answer:"""
        
        inputs = self.tokenizer(
            prompt,
            max_length=512,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.generator_model.generate(
                input_ids=inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                max_length=max_length,
                num_beams=4,
                early_stopping=True,
                temperature=0.7,
                top_p=0.95,
                do_sample=True
            )
        
        answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Compute overall confidence
        avg_score = np.mean([c['reranking_score'] for c in selected])
        
        return {
            'answer': answer.strip(),
            'context': [
                {
                    'question': c['question'],
                    'answer': c['answer'],
                    'score': c['reranking_score']
                }
                for c in selected
            ],
            'confidence': float(avg_score),
            'sources': [c['index'] for c in selected],
            'pipeline_metrics': {
                'retrieval_candidates': len(candidates),
                'final_context_count': len(selected),
                'avg_reranking_score': float(avg_score)
            }
        }

    def batch_evaluate(
        self,
        test_queries: List[str],
        reference_answers: Optional[List[str]] = None
    ) -> Dict:
        """
        Batch evaluate the QA tool on multiple queries.
        
        Args:
            test_queries: List of questions to answer
            reference_answers: Optional reference answers for scoring
        
        Returns:
            Evaluation results with semantic similarity scores
        """
        from sklearn.metrics.pairwise import cosine_similarity
        
        results = {
            'total_queries': len(test_queries),
            'successful_answers': 0,
            'failed_answers': 0,
            'avg_confidence': 0.0,
            'semantic_similarities': [],
            'detailed_results': []
        }
        
        confidence_scores = []
        
        for i, query in enumerate(test_queries):
            try:
                result = self.ask(query)
                results['successful_answers'] += 1
                confidence_scores.append(result['confidence'])
                
                detail = {
                    'query': query,
                    'answer': result['answer'],
                    'confidence': result['confidence'],
                    'context_count': len(result['context'])
                }
                
                # If reference answer provided, compute semantic similarity
                if reference_answers and i < len(reference_answers):
                    gen_emb = self.embedder.encode([result['answer']], convert_to_numpy=True)
                    ref_emb = self.embedder.encode([reference_answers[i]], convert_to_numpy=True)
                    
                    sim = cosine_similarity(gen_emb, ref_emb)[0][0]
                    detail['semantic_similarity'] = float(sim)
                    results['semantic_similarities'].append(float(sim))
                
                results['detailed_results'].append(detail)
                
            except Exception as e:
                logger.error(f"Failed to answer query {i+1}: {str(e)}")
                results['failed_answers'] += 1
        
        if confidence_scores:
            results['avg_confidence'] = float(np.mean(confidence_scores))
        
        if results['semantic_similarities']:
            results['avg_semantic_similarity'] = float(np.mean(results['semantic_similarities']))
        
        return results


def load_knowledge_base_from_json(file_path: str) -> List[Dict]:
    """Load military retirement Q&A knowledge base from JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Knowledge base file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'qa_pairs' in data:
        return data['qa_pairs']
    else:
        raise ValueError("Knowledge base JSON must contain list of Q&A pairs or 'qa_pairs' key")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create sample knowledge base
    sample_kb = [
        {
            'question': 'What is the survivor benefit plan?',
            'answer': 'The Survivor Benefit Plan (SBP) is an optional monthly income stream...'
        },
        {
            'question': 'How much is my military retirement pay?',
            'answer': 'Your military retirement pay is calculated as: 2.5% × Years of Service × Final Basic Pay...'
        }
    ]
    
    # Initialize tool
    tool = MilitaryRetirementQATool(sample_kb, device='cpu')
    
    # Ask a question
    result = tool.ask("What happens to my TSP after retirement?")
    print(f"Answer: {result['answer']}")
    print(f"Confidence: {result['confidence']:.2%}")
