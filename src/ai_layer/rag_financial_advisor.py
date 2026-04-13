"""
RAG Financial Advisor - Hybrid RAG Integration for ProjectAtlas
===============================================================

This module provides the RAG layer for ProjectAtlas FinancialCoach.
It retrieves evidence-backed answers from the 561-pair military finance knowledge base
and routes questions based on confidence thresholds.

Architecture:
- Module: AI Layer (Adapter Pattern)
- Integration: Hybrid RAG (RAG + Intent-Based Fallback)
- Knowledge Base: 561 Q&A pairs (Milestone E, production-ready)
- Primary Models: FLAN-T5-base + Hybrid RAG pipeline
- Device: CPU-only (validated in Milestone E)

Usage:
    from src.ai_layer.rag_financial_advisor import RAGFinancialAdvisor
    
    advisor = RAGFinancialAdvisor(config='production')
    result = advisor.retrieve_knowledge("What's my estimated retirement pay?")
    
    # Returns: {
    #     "answer": str,
    #     "confidence": float,
    #     "sources": list,
    #     "retrieval_time_ms": float,
    #     "routing_decision": str  # "rag" or "fallback"
    # }
"""

import os
import json
import logging
import time
import pickle
from pathlib import Path
from typing import Dict, Optional, List, Any
import numpy as np
from datetime import datetime

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from sentence_transformers import SentenceTransformer, CrossEncoder
    import faiss
except ImportError as e:
    raise ImportError(
        f"Required packages not installed. Install with:\n"
        f"  pip install torch transformers sentence-transformers faiss-cpu"
    ) from e

# Configure logging
logger = logging.getLogger('RAGFinancialAdvisor')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RAGFinancialAdvisor:
    """
    Milestone E RAG System adapter for ProjectAtlas FinancialCoach.
    
    Provides retrieval-augmented generation for military retirement questions.
    Implements confidence-based routing between RAG retrieval and fallback strategies.
    """
    
    # Production hyperparameters (locked from Milestone E Phase 1 testing)
    HYPERPARAMETERS = {
        'retrieval_k': 1,
        'similarity_threshold': 0.7,
        'weak_category_amplifier': 3.0,
        'max_generation_length': 256,
        'confidence_threshold': 0.7,  # Route threshold: RAG if >= 0.7, else fallback
    }
    
    # Weak categories requiring amplification
    WEAK_CATEGORIES = {'integration', 'survivor_benefits', 'tax', 'special_pay'}
    
    def __init__(
        self,
        config: str = 'production',
        kb_path: Optional[Path] = None,
        index_path: Optional[Path] = None,
        embeddings_path: Optional[Path] = None,
    ):
        """
        Initialize RAG Financial Advisor with graceful degradation.
        
        If RAG artifacts are missing, system falls back to FLAN-T5 only.
        
        Args:
            config: 'production' (default) or 'development'
            kb_path: Path to knowledge base JSON (auto-detected if None)
            index_path: Path to FAISS index pickle (auto-detected if None)
            embeddings_path: Path to embeddings npz (auto-detected if None)
        """
        self.config = config
        self.device = torch.device('cpu')  # Force CPU for consistency with Milestone E
        os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Disable CUDA globally
        
        # Auto-detect artifact paths if not provided
        self.data_dir = Path(__file__).parent.parent.parent / 'data'
        self.kb_path = kb_path or (self.data_dir / 'milestone_e_knowledge_base.json')
        self.index_path = index_path or (self.data_dir / 'milestone_e_faiss_index.pkl')
        self.embeddings_path = embeddings_path or (self.data_dir / 'milestone_e_kb_embeddings.npz')
        
        logger.info(f"Initializing RAGFinancialAdvisor (config={config})")
        
        # Flag for graceful degradation
        self.rag_available = False
        
        try:
            # Load knowledge base
            self._load_knowledge_base()
            
            # Load models
            self._load_models()
            
            # Load FAISS index and embeddings
            self._load_indexes()
            
            self.rag_available = True
            logger.info("✅ RAGFinancialAdvisor initialized successfully with RAG support")
            
        except FileNotFoundError as e:
            logger.warning(
                f"⚠️ RAG knowledge base not found ({e}). "
                "Falling back to FLAN-T5 only. "
                "For full RAG support, ensure data/ files are present."
            )
            self.rag_available = False
            self.knowledge_base = []
            self.faiss_index = None
            
        except Exception as e:
            logger.warning(
                f"⚠️ RAG initialization failed: {e}. "
                "Falling back to FLAN-T5 only."
            )
            self.rag_available = False
            self.knowledge_base = []
            self.faiss_index = None
    
    def _load_knowledge_base(self) -> None:
        """Load 561-pair knowledge base from JSON."""
        logger.info(f"Loading knowledge base from {self.kb_path}...")
        
        if not self.kb_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {self.kb_path}")
        
        with open(self.kb_path, 'r') as f:
            data = json.load(f)
        
        self.knowledge_base = data['pairs']
        self.metadata = data['metadata']
        self.category_dist = data.get('category_distribution', {})
        
        logger.info(
            f"✅ Loaded {len(self.knowledge_base)} Q&A pairs, "
            f"{len(self.category_dist)} categories"
        )
    
    def _load_models(self) -> None:
        """Load embedding, cross-encoder, and generator models."""
        logger.info("Loading ML models...")
        
        try:
            # Embedder
            logger.info("  Loading embedder (all-MiniLM-L6-v2)...")
            self.embedder = SentenceTransformer(
                'sentence-transformers/all-MiniLM-L6-v2',
                device=str(self.device)
            )
            self.embedder.eval()
            
            # Cross-encoder for reranking
            logger.info("  Loading cross-encoder (ms-marco-MiniLM-L-6-v2)...")
            self.cross_encoder = CrossEncoder(
                'cross-encoder/ms-marco-MiniLM-L-6-v2',
                device=str(self.device),
                max_length=256
            )
            self.cross_encoder.eval()
            
            # T5 generator
            logger.info("  Loading generator (flan-t5-base)...")
            self.tokenizer = AutoTokenizer.from_pretrained('google/flan-t5-base')
            self.generator = AutoModelForSeq2SeqLM.from_pretrained(
                'google/flan-t5-base'
            )
            self.generator.to(self.device)
            self.generator.eval()
            
            logger.info("✅ All models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    def _load_indexes(self) -> None:
        """Load FAISS index and KB embeddings."""
        logger.info("Loading FAISS index and embeddings...")
        
        # Load FAISS index
        if not self.index_path.exists():
            raise FileNotFoundError(f"FAISS index not found: {self.index_path}")
        
        with open(self.index_path, 'rb') as f:
            self.faiss_index = pickle.load(f)
        
        logger.info(f"✅ FAISS index loaded ({self.faiss_index.ntotal} vectors)")
        
        # Load KB embeddings
        if not self.embeddings_path.exists():
            raise FileNotFoundError(f"Embeddings not found: {self.embeddings_path}")
        
        embeddings_data = np.load(self.embeddings_path)
        self.kb_embeddings = embeddings_data['embeddings']
        
        logger.info(f"✅ KB embeddings loaded (shape: {self.kb_embeddings.shape})")
    
    def retrieve_knowledge(
        self,
        query: str,
        return_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve evidence-backed answer from RAG system.
        
        Implements full retrieval pipeline:
        1. Embed user query
        2. Search FAISS index for relevant KB pairs
        3. Rerank with cross-encoder
        4. Generate answer using T5
        5. Return with confidence score for routing decision
        
        If RAG is unavailable, returns empty response indicating fallback needed.
        
        Args:
            query: User's question
            return_sources: Include source Q&A pair in response
        
        Returns:
            {
                "answer": str,                 # Generated answer from T5
                "confidence": float,           # Retrieval confidence score [0, 1]
                "sources": list,               # Relevant KB pairs
                "retrieval_time_ms": float,    # Total pipeline latency
                "routing_decision": str,       # "rag" (use answer) or "fallback"
                "evidence": str,               # Raw context passed to T5
            }
        """
        start_time = time.time()
        
        # Check if RAG is available
        if not self.rag_available:
            logger.debug("RAG not available, returning fallback signal")
            return {
                'answer': '',
                'confidence': 0.0,
                'sources': [],
                'retrieval_time_ms': (time.time() - start_time) * 1000,
                'routing_decision': 'fallback',
                'evidence': '',
                'rag_available': False,
            }
        
        try:
            # 1. Embed query
            query_embedding = self.embedder.encode(
                query,
                convert_to_numpy=True
            ).reshape(1, -1).astype(np.float32)
            
            # 2. Search FAISS index (k=1)
            distances, indices = self.faiss_index.search(
                query_embedding,
                self.HYPERPARAMETERS['retrieval_k']
            )
            
            top_idx = indices[0][0]
            raw_distance = distances[0][0]
            
            # Convert L2 distance to similarity score
            similarity_score = 1.0 / (1.0 + raw_distance)
            
            # 3. Rerank with cross-encoder
            retrieved_pair = self.knowledge_base[top_idx]
            rerank_input = [query, retrieved_pair['answer']]
            rerank_score = self.cross_encoder.predict([rerank_input])[0]
            rerank_score = float(rerank_score)
            
            # Normalize cross-encoder score to [0, 1] using sigmoid
            # Raw cross-encoder scores can exceed [0, 1], so normalize: 1/(1+e^-x)
            rerank_score = 1.0 / (1.0 + np.exp(-rerank_score))
            
            # 4. Determine routing decision based on confidence threshold
            final_confidence = max(similarity_score, rerank_score)
            threshold = self.HYPERPARAMETERS['confidence_threshold']
            routing_decision = 'rag' if final_confidence >= threshold else 'fallback'
            
            # 5. Generate answer with T5
            context = f"Question: {retrieved_pair['question']}\nAnswer: {retrieved_pair['answer']}"
            inputs = self.tokenizer(
                f"Generate answer for: {query}\nContext: {context}",
                return_tensors="pt",
                max_length=256,
                truncation=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.generator.generate(
                    **inputs,
                    max_length=self.HYPERPARAMETERS['max_generation_length'],
                    num_beams=4,
                    early_stopping=True
                )
            
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Calculate latency
            retrieval_time_ms = (time.time() - start_time) * 1000
            
            # Prepare response
            response = {
                'answer': answer,
                'confidence': float(final_confidence),
                'retrieval_score': float(similarity_score),
                'rerank_score': float(rerank_score),
                'routing_decision': routing_decision,
                'evidence': context,
                'sources': [retrieved_pair] if return_sources else [],
                'retrieval_time_ms': float(retrieval_time_ms),
                'metadata': {
                    'query': query,
                    'kb_pair_index': int(top_idx),
                    'threshold': threshold,
                    'confidence_threshold': threshold,
                }
            }
            
            logger.debug(
                f"✅ Retrieved: confidence={final_confidence:.3f}, "
                f"routing={routing_decision}, latency={retrieval_time_ms:.1f}ms"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}", exc_info=True)
            return {
                'answer': None,
                'confidence': 0.0,
                'routing_decision': 'fallback',
                'error': str(e),
                'retrieval_time_ms': (time.time() - start_time) * 1000,
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Return adapter status and metadata."""
        return {
            'status': 'ready',
            'config': self.config,
            'device': str(self.device),
            'kb_size': len(self.knowledge_base),
            'categories': len(self.category_dist),
            'models': {
                'embedder': 'all-MiniLM-L6-v2',
                'cross_encoder': 'ms-marco-MiniLM-L-6-v2',
                'generator': 'flan-t5-base',
            },
            'hyperparameters': self.HYPERPARAMETERS,
            'metadata': self.metadata,
        }
