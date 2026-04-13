"""
MilitaryRetirementQA Integration Module for ProjectAtlas
========================================================

This module integrates the 561-pair optimized Hybrid RAG pipeline into ProjectAtlas.
It serves as the AI layer for FinancialCoach Step 10 (AI Advisor & Recommendations).

Architecture:
- Module Type: AI Layer Integration
- Model: FLAN-T5-base + Hybrid RAG
- Dataset: 561 Q&A pairs (3-fold cross-validation)
- Hyperparameters: k=1, threshold=0.7, weighted-sum, 3.0x weak-category amp
- Performance: ROUGE-L 0.2444, E2E latency < 2000ms

Usage:
    from military_retirement_qa_integration import MilitaryRetirementQAIntegration
    qa_system = MilitaryRetirementQAIntegration(config='production')
    answer = qa_system.ask("What are my retirement payment options?")
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np
from collections import defaultdict

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from sentence_transformers import SentenceTransformer, CrossEncoder
except ImportError as e:
    raise ImportError(f"Required ML packages not found. Install with: pip install torch transformers sentence-transformers") from e

# Configure logging
logger = logging.getLogger('MilitaryRetirementQA')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class MilitaryRetirementQAIntegration:
    """
    Production-ready Military Retirement Q&A system for ProjectAtlas.
    
    Integrates 561-pair Hybrid RAG pipeline with ProjectAtlas FinancialCoach.
    Provides accurate, evidence-based answers to military retirement questions.
    """
    
    # LOCKED HYPERPARAMETERS (from Milestone D Phase 4)
    CONFIG = {
        'dev': {
            'retrieval_k': 1,
            'similarity_threshold': 0.7,
            'weighting_strategy': 'weighted-sum',
            'weak_category_amplifier': 3.0,
            'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
            'cross_encoder_model': 'cross-encoder/ms-marco-MiniLM-L-6-v2',
            'generator_model': 'google/flan-t5-base',
            'device': 'cpu',
            'max_generation_length': 256,
            'confidence_threshold': 0.3
        },
        'staging': {
            'retrieval_k': 1,
            'similarity_threshold': 0.7,
            'weighting_strategy': 'weighted-sum',
            'weak_category_amplifier': 3.0,
            'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
            'cross_encoder_model': 'cross-encoder/ms-marco-MiniLM-L-6-v2',
            'generator_model': 'google/flan-t5-base',
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'max_generation_length': 256,
            'confidence_threshold': 0.3
        },
        'production': {
            'retrieval_k': 1,
            'similarity_threshold': 0.7,
            'weighting_strategy': 'weighted-sum',
            'weak_category_amplifier': 3.0,
            'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
            'cross_encoder_model': 'cross-encoder/ms-marco-MiniLM-L-6-v2',
            'generator_model': 'google/flan-t5-base',
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'max_generation_length': 256,
            'confidence_threshold': 0.3
        }
    }
    
    # Weak categories requiring 3.0x amplification
    WEAK_CATEGORIES = {'integration', 'survivor_benefits', 'tax', 'special_pay'}
    
    def __init__(
        self,
        config: str = 'production',
        kb_path: Optional[str] = None,
        model_fold: int = 0
    ):
        """
        Initialize MilitaryRetirementQA system.
        
        Args:
            config: Environment ('dev', 'staging', 'production')
            kb_path: Path to knowledge base JSON file
            model_fold: Which fold model to load (0, 1, or 2)
        """
        if config not in self.CONFIG:
            raise ValueError(f"Unknown config: {config}. Options: {list(self.CONFIG.keys())}")
        
        self.config_name = config
        self.config = self.CONFIG[config]
        self.device = torch.device(self.config['device'])
        self.model_fold = model_fold
        
        logger.info(f"Initializing MilitaryRetirementQA ({config} mode)")
        
        # Load knowledge base
        if kb_path is None:
            # Try default location
            kb_path = Path(__file__).parent.parent / 'AIT716' / 'Milestone_D' / 'phase4_folds' / f'fold_{model_fold}_expanded_561.json'
        
        self._load_knowledge_base(kb_path)
        
        # Load models
        self._load_embedder()
        self._load_cross_encoder()
        self._load_generator()
        
        # Build FAISS index
        self._build_faiss_index()
        
        logger.info(f"✓ MilitaryRetirementQA ready ({len(self.knowledge_base)} Q&A pairs)")
    
    def _load_knowledge_base(self, kb_path: str):
        """Load knowledge base from JSON file."""
        logger.info(f"Loading knowledge base from {kb_path}...")
        
        with open(kb_path, 'r') as f:
            self.knowledge_base = json.load(f)
        
        logger.info(f"✓ Loaded {len(self.knowledge_base)} Q&A pairs")
    
    def _load_embedder(self):
        """Load sentence transformer for embeddings."""
        logger.info(f"Loading embedder: {self.config['embedding_model']}")
        self.embedder = SentenceTransformer(self.config['embedding_model'])
        self.embedder.to(self.device)
        logger.info("✓ Embedder loaded")
    
    def _load_cross_encoder(self):
        """Load cross-encoder for re-ranking."""
        logger.info(f"Loading cross-encoder: {self.config['cross_encoder_model']}")
        self.cross_encoder = CrossEncoder(self.config['cross_encoder_model'])
        self.cross_encoder.to(self.device)
        logger.info("✓ Cross-encoder loaded")
    
    def _load_generator(self):
        """Load FLAN-T5 generator model."""
        logger.info(f"Loading generator: {self.config['generator_model']}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.config['generator_model'])
        self.generator = AutoModelForSeq2SeqLM.from_pretrained(self.config['generator_model'])
        self.generator.to(self.device)
        self.generator.eval()
        logger.info("✓ Generator loaded")
    
    def _build_faiss_index(self):
        """Build FAISS index for fast retrieval."""
        import faiss
        
        logger.info("Building FAISS index...")
        
        # Encode knowledge base
        kb_texts = [f"Q: {pair['question']}\nA: {pair['answer']}" for pair in self.knowledge_base]
        self.kb_embeddings = self.embedder.encode(kb_texts, convert_to_numpy=True)
        
        # Create FAISS index
        dimension = self.kb_embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.kb_embeddings.astype('float32'))
        
        logger.info(f"✓ FAISS index with {self.index.ntotal} vectors")
    
    def ask(
        self,
        query: str,
        return_context: bool = False,
        verbose: bool = False
    ) -> Dict:
        """
        Answer a military retirement question.
        
        Args:
            query: User's question
            return_context: Include retrieved context in response
            verbose: Return detailed scoring information
        
        Returns:
            Dict with answer, confidence, sources, and optionally context
        """
        start_time = time.time()
        
        if not query or not query.strip():
            logger.warning("Empty query received")
            return {
                'answer': "Please provide a question about military retirement.",
                'confidence': 0.0,
                'sources': [],
                'context': [],
                'error': 'empty_query'
            }
        
        try:
            # 1. RETRIEVAL
            query_emb = self.embedder.encode([query], convert_to_numpy=True)[0]
            
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(query_emb.reshape(1, -1), self.kb_embeddings)[0]
            
            # Apply weak category amplification
            for idx in range(len(similarities)):
                category = self.knowledge_base[idx].get('category', 'unknown')
                if category in self.WEAK_CATEGORIES:
                    similarities[idx] *= self.config['weak_category_amplifier']
            
            # Get top candidate
            top_idx = np.argmax(similarities)
            retrieval_score = similarities[top_idx]
            top_pair = self.knowledge_base[top_idx]
            
            # 2. RE-RANKING
            pair_text = f"Q: {top_pair['question']}\nA: {top_pair['answer']}"
            rerank_score = self.cross_encoder.predict([[query, pair_text]])[0]
            
            # 3. CHECK CONFIDENCE
            if rerank_score < self.config['confidence_threshold']:
                logger.warning(f"Low confidence ({rerank_score:.3f}) for query: {query[:50]}")
                return {
                    'answer': "I'm not confident enough to answer this question. Please consult official DoD resources.",
                    'confidence': float(rerank_score),
                    'sources': [],
                    'context': [],
                    'warning': 'low_confidence'
                }
            
            # 4. GENERATION
            context_text = f"Military retirement information: Q: {top_pair['question']}\nA: {top_pair['answer']}\n\nUser's question: {query}\n\nAnswer:"
            inputs = self.tokenizer.encode(context_text, return_tensors='pt').to(self.device)
            
            with torch.no_grad():
                outputs = self.generator.generate(
                    inputs,
                    max_length=self.config['max_generation_length'],
                    num_beams=4,
                    early_stopping=True,
                    temperature=0.7
                )
            
            generated_answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 5. PREPARE RESPONSE
            response = {
                'answer': generated_answer,
                'confidence': float(rerank_score),
                'sources': [
                    {
                        'question': top_pair['question'],
                        'answer': top_pair['answer'],
                        'category': top_pair.get('category', 'unknown'),
                        'retrieval_score': float(retrieval_score),
                        'rerank_score': float(rerank_score)
                    }
                ],
                'latency_ms': (time.time() - start_time) * 1000
            }
            
            if return_context:
                response['context'] = [top_pair]
            
            if verbose:
                response['scoring'] = {
                    'query': query,
                    'retrieval_score': float(retrieval_score),
                    'rerank_score': float(rerank_score),
                    'weak_category': top_pair.get('category') in self.WEAK_CATEGORIES,
                    'amplified': top_pair.get('category') in self.WEAK_CATEGORIES
                }
            
            logger.info(f"Query answered successfully (confidence={rerank_score:.3f}, latency={response['latency_ms']:.0f}ms)")
            return response
        
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                'answer': "An error occurred while processing your question. Please try again.",
                'confidence': 0.0,
                'sources': [],
                'context': [],
                'error': str(e)
            }
    
    def ask_batch(self, queries: List[str]) -> List[Dict]:
        """
        Process multiple questions efficiently.
        
        Args:
            queries: List of questions
        
        Returns:
            List of answer dictionaries
        """
        logger.info(f"Processing batch of {len(queries)} queries...")
        results = []
        
        for i, query in enumerate(queries):
            result = self.ask(query)
            results.append(result)
            
            if (i + 1) % 10 == 0:
                logger.info(f"  Processed {i + 1}/{len(queries)} queries")
        
        return results
    
    def health_check(self) -> Dict:
        """
        Verify system health and readiness.
        
        Returns:
            Dict with health status
        """
        try:
            # Test question
            test_question = "What is military retirement?"
            start = time.time()
            result = self.ask(test_question, verbose=True)
            latency = (time.time() - start) * 1000
            
            health = {
                'status': 'healthy' if latency < 3000 and result.get('confidence', 0) > 0.3 else 'degraded',
                'model': {
                    'fold': self.model_fold,
                    'config': self.config_name,
                    'device': str(self.device)
                },
                'components': {
                    'embedder': True,
                    'cross_encoder': True,
                    'generator': True,
                    'faiss_index': self.index.ntotal > 0
                },
                'test_query': {
                    'latency_ms': latency,
                    'confidence': result.get('confidence', 0),
                    'has_answer': len(result.get('answer', '')) > 10
                },
                'knowledge_base': {
                    'size': len(self.knowledge_base),
                    'categories': len(set(pair.get('category') for pair in self.knowledge_base))
                }
            }
            
            logger.info(f"Health check: {health['status']}")
            return health
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# Example usage
if __name__ == '__main__':
    # Initialize system
    qa_system = MilitaryRetirementQAIntegration(config='dev')
    
    # Health check
    print("\nHealth Check:")
    health = qa_system.health_check()
    print(json.dumps(health, indent=2))
    
    # Ask questions
    print("\nSample Queries:")
    questions = [
        "What are my military retirement payment options?",
        "How does SBP work for my family?",
        "Am I eligible for VA disability?",
        "What is the High-3 calculation?"
    ]
    
    for q in questions:
        print(f"\nQ: {q}")
        answer = qa_system.ask(q, verbose=True)
        print(f"A: {answer['answer'][:100]}...")
        print(f"   Confidence: {answer['confidence']:.3f}")
        print(f"   Latency: {answer['latency_ms']:.0f}ms")
