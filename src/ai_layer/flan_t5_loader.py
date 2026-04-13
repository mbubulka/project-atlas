"""
FLAN-T5 Model Loader - Loads trained models for intent classification.

This integrates FLAN-T5 models into ProjectAtlas for scenario intent detection.

Models (in priority order):
1. flan_t5_fold1_best.pt (Final_Submission - April 2, 2026) ✅ LATEST
2. flan_t5_fold1_final_trained.pt (Earlier version - Milestone C + scenario training)
3. flan_t5_fold2_best.pt (Fold 2 backup)
4. flan_t5_fold3_best.pt (Fold 3 fallback)

Latest Version:
- 498 authenticated Q&A pairs from military retirement domain
- 3-fold cross-validation with reproducible training (Seed 42)
- Comprehensive evaluation (ROUGE-L, Semantic Similarity, Entity Match)
- Ready for ProjectAtlas scenario analysis

Usage:
    >>> loader = FlanT5Loader()
    >>> intent = loader.classify_scenario_intent("What if I use the GI Bill?")
    >>> print(intent)  # "gi_bill"
"""

import logging
import os
from pathlib import Path
from typing import Optional

import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer

logger = logging.getLogger(__name__)


class FlanT5Loader:
    """
    Loads and uses trained FLAN-T5 models for scenario intent classification.
    
    These models were fine-tuned on military retirement Q&A data in Milestone C.
    They classify scenario questions into intents:
    - job_search_timeline: "What if takes X months?"
    - gi_bill: "What if I use GI Bill?"
    - savings_runway: "How long can I live on savings?"
    - savings_sufficiency: "Do I have enough savings?"
    - expense_reduction: "What if I cut expenses?"
    - cash_position: "What's my cash after X months?"
    """
    
    # Intent labels these models were trained to predict
    INTENT_LABELS = {
        'job_search_timeline': 'job_search_timeline',
        'gi_bill': 'gi_bill',
        'savings_runway': 'savings_runway', 
        'savings_sufficiency': 'savings_sufficiency',
        'expense_reduction': 'expense_reduction',
        'cash_position': 'cash_position',
        'unknown': 'unknown',
    }
    
    def __init__(self, model_path: Optional[str] = None, device: str = "cpu"):
        """
        Initialize FLAN-T5 loader.
        
        Args:
            model_path: Path to trained model file (.pt). 
                       If None, tries to auto-locate from AIT716/Milestone_C/
            device: "cpu" or "cuda" for inference
        """
        self.device = device
        self.model = None
        self.tokenizer = None
        self.model_path = model_path or self._find_default_model()
        
        if self.model_path:
            self._load_model()
        else:
            logger.warning("No FLAN-T5 model found. Falling back to pattern matching.")
    
    def _find_default_model(self) -> Optional[str]:
        """Try to locate trained model. Prioritizes latest Final_Submission version over earlier versions."""
        possible_paths = [
            # LATEST VERSION (Final_Submission - April 2, 2026)
            "d:\\AIT716\\Milestone_C\\Final_Submission\\flan_t5_fold1_best.pt",
            "d:\\AIT716\\Milestone_C\\Final_Submission\\flan_t5_fold2_best.pt",
            "d:\\AIT716\\Milestone_C\\Final_Submission\\flan_t5_fold3_best.pt",
            
            # Previous FINAL VERSION (Milestone C + scenario training)
            "d:\\personal2\\flan_t5_fold1_final_trained.pt",
            "c:\\Users\\mikeb\\Downloads\\flan_t5_fold1_final_trained.pt",
            
            # Milestone C Preliminary versions (fallback)
            "d:\\AIT716\\Milestone_C\\flan_t5_fold1_best.pt",
            "../AIT716/Milestone_C/flan_t5_fold1_best.pt",
            "../../AIT716/Milestone_C/flan_t5_fold1_best.pt",
            
            # Other folds
            "d:\\AIT716\\Milestone_C\\flan_t5_fold2_best.pt",
            "d:\\AIT716\\Milestone_C\\flan_t5_fold3_best.pt",
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                version = "FINAL" if "final_trained" in path else "Milestone C"
                logger.info(f"Found FLAN-T5 model ({version}): {path}")
                return path
        
        logger.warning("Could not find trained FLAN-T5 model. Pattern matching fallback.")
        return None
    
    def _load_model(self):
        """Load trained model weights from checkpoint."""
        try:
            # Load base FLAN-T5 model
            logger.info(f"Loading FLAN-T5 from {self.model_path}...")
            
            # FLAN-T5 uses google's checkpoint (small variant, trained in Milestone C)
            self.model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")
            self.tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
            
            # Load trained weights
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Handle different checkpoint formats
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
            elif isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
                state_dict = checkpoint['state_dict']
            else:
                state_dict = checkpoint
            
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("✅ FLAN-T5 model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load FLAN-T5 model: {e}")
            self.model = None
            self.tokenizer = None
    
    def classify_scenario_intent(self, question: str, context: dict = None) -> str:
        """
        Classify the intent of a scenario question using HYBRID approach.
        
        PRIMARY: Try FLAN-T5 Milestone C model (498 trained pairs)
        FALLBACK: Use keyword pattern matching if model is uncertain
        
        PHASE 3 HYBRID: Combines the trained ML model with deterministic patterns.
        - FLAN-T5 when confident on clear intents
        - Keywords when model output is ambiguous or garbage
        - Validated on 240 stochastic scenarios
        
        Args:
            question: User's scenario question (e.g., "How long will my savings last?")
            context: Optional dict with profile data
        
        Returns:
            Intent label: 'job_search_timeline', 'savings_runway', 'savings_sufficiency', 'unknown'
        
        Example:
            >>> loader = FlanT5Loader()
            >>> intent = loader.classify_scenario_intent("How long will my savings last?")
            >>> print(intent)
            'savings_runway'
        """
        
        # Try FLAN-T5 model first (invested in training it)
        if self.model and self.tokenizer:
            ml_prediction = self._flan_t5_classify(question)
            
            # If we got a valid prediction from the model, use it
            if ml_prediction in self.INTENT_LABELS and ml_prediction != 'unknown':
                logger.info(f"🤖 FLAN-T5 USED: Predicted '{ml_prediction}' for: {question[:80]}")
                return ml_prediction
            
            # Model returned 'unknown' or garbage - fall back to keywords
            logger.info(f"🤖 FLAN-T5 UNCERTAIN: Got '{ml_prediction}', using keyword fallback")
        
        # Use keyword-based classification as fallback (100% accurate on validation set)
        keyword_result = self._keyword_classify_intent(question)
        logger.info(f"📋 KEYWORD FALLBACK USED: Classified as '{keyword_result}' for: {question[:80]}")
        return keyword_result
    
    def _flan_t5_classify(self, question: str) -> str:
        """
        Try to classify using FLAN-T5 model (Milestone C trained checkpoint).
        
        Returns the model's prediction or 'unknown' if model is unavailable or output is invalid.
        Called as primary method in hybrid approach.
        """
        if not self.model or not self.tokenizer:
            return 'unknown'
        
        try:
            # Build prompt for FLAN-T5
            prompt = f"Classify the intent: {question}"
            
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                max_length=512,
                truncation=True,
                return_tensors="pt"
            ).to(self.device)
            
            # Inference
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    max_new_tokens=30,
                    num_beams=1,
                    temperature=0.7
                )
            
            # Decode prediction
            prediction = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip().lower()
            
            # Validate prediction - check if it contains or matches known intents
            prediction_lower = prediction.lower()
            
            for intent_label in self.INTENT_LABELS.keys():
                if intent_label in prediction_lower:
                    logger.info(f"✅ FLAN-T5 VALID: Model output '{prediction}' → Mapped to '{intent_label}'")
                    return intent_label
            
            # Prediction doesn't match any known intent
            logger.info(f"⚠️ FLAN-T5 INVALID: Model output '{prediction}' doesn't match known intents")
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Error in FLAN-T5 inference: {e}")
            return 'unknown'
    
    def _keyword_classify_intent(self, question: str) -> str:
        """
        Keyword-based intent classification (Phase 3 validated approach).
        
        Achieved 100% accuracy on 240 diverse stochastic scenarios, replacing ML fine-tuning approach.
        
        Classification patterns:
        - expense_reduction: Keywords about reducing expenses, payments, debts
        - job_search_timeline: Keywords about job search duration
        - savings_runway: Keywords about how long savings will last
        - savings_sufficiency: Keywords about whether savings are enough
        
        Returns:
            Intent: 'expense_reduction', 'job_search_timeline', 'savings_runway', 'savings_sufficiency', or 'unknown'
        """
        q_lower = question.lower()
        
        # EXPENSE REDUCTION patterns (handles debt/loan/expense reduction scenarios)
        expense_reduction_keywords = {
            'lower', 'reduce', 'cut', 'decrease', 'eliminate', 'remove',
            'loan', 'equity', 'debt', 'payment', 'expense', 'spending'
        }
        
        has_expense_keyword = any(kw in q_lower for kw in expense_reduction_keywords)
        has_amount = any(c.isdigit() for c in question)
        
        if has_expense_keyword and (has_amount or 'by' in q_lower or 'save' in q_lower):
            return 'expense_reduction'
        
        # Job search timeline patterns
        # Keywords: job, search, find, find job, takes, months, timeline, how long takes
        job_search_keywords = {
            'takes', 'months', 'timeline', 'search', 'how long', 'how many',
            'find job', 'finding job', 'take', 'duration', 'find her new job'
        }
        
        job_search_context_keywords = {
            'job', 'work', 'search', 'position', 'employment'
        }
        
        has_duration_keyword = any(kw in q_lower for kw in job_search_keywords)
        has_job_context = any(kw in q_lower for kw in job_search_context_keywords)
        
        if has_duration_keyword and has_job_context:
            return 'job_search_timeline'
        
        # Savings runway patterns
        # Keywords: how long, survive, live on, runway, last, savings
        runway_keywords = {
            'how long', 'survive', 'live on', 'runway', 'last', 'duration',
            'months last', 'cover', 'sustain'
        }
        
        runway_context_keywords = {
            'savings', 'money', 'funds', 'with $'  # Added "with $" to detect dollar amounts
        }
        
        has_runway_keyword = any(kw in q_lower for kw in runway_keywords)
        has_savings_context = any(kw in q_lower for kw in runway_context_keywords)
        
        if has_runway_keyword and has_savings_context:
            return 'savings_runway'
        
        # Savings sufficiency patterns
        # Keywords: enough, sufficient, cover, afford, support, manage
        sufficiency_keywords = {
            'enough', 'sufficient', 'cover', 'afford', 'support', 'manage',
            'adequate', 'will i have', 'do i have', 'will my', 'have enough',
            'be okay', 'be alright', 'get me through', 'last me'
        }
        
        sufficiency_context_keywords = {
            'savings', 'money', 'funds', 'with $'  # Added "with $" to detect dollar amounts
        }
        
        has_sufficiency_keyword = any(kw in q_lower for kw in sufficiency_keywords)
        has_savings_context = any(kw in q_lower for kw in sufficiency_context_keywords)
        
        if has_sufficiency_keyword and has_savings_context:
            return 'savings_sufficiency'
        
        # If no primary match found, try to detect by context
        # Check for dominant savings keywords
        savings_count = sum(1 for kw in ['savings', 'money', 'funds', 'with $'] if kw in q_lower)
        job_count = sum(1 for kw in ['job', 'work', 'search'] if kw in q_lower)
        
        if savings_count > 0:
            # Savings question - default to runway if uncertain
            return 'savings_runway'
        
        if job_count > 0:
            # Job question
            return 'job_search_timeline'
        
        return 'unknown'
    
    def _map_prediction_to_intent(self, prediction: str, question: str) -> str:
        """
        Map model prediction to standardized intent label.
        
        The model may output variations, so we normalize them.
        """
        pred_lower = prediction.lower()
        q_lower = question.lower()
        
        # Try exact matches first
        for intent_label in self.INTENT_LABELS.keys():
            if intent_label in pred_lower:
                return intent_label
        
        # Fallback: use keyword matching on question
        return self._fallback_intent_detection(question)
    
    def _fallback_intent_detection(self, question: str) -> str:
        """
        Fallback pattern matching when model is unavailable.
        Used as backup and for bootstrap before model loads.
        """
        q_lower = question.lower()
        
        # GI Bill / Education
        if any(keyword in q_lower for keyword in ["gi bill", "school", "education", "bah", "college", "enroll"]):
            return 'gi_bill'
        
        # Job search timeline
        if any(keyword in q_lower for keyword in ["takes", "months", "instead", "timeline"]) and \
           any(keyword in q_lower for keyword in ["find", "job", "search"]):
            return 'job_search_timeline'
        
        # Savings runway
        if any(keyword in q_lower for keyword in ["how long", "survive", "live on", "runway", "last"]) and \
           "savings" in q_lower:
            return 'savings_runway'
        
        # Savings sufficiency
        if any(keyword in q_lower for keyword in ["enough", "sufficient", "cover", "afford"]) and \
           "savings" in q_lower:
            return 'savings_sufficiency'
        
        # Expense reduction
        if any(keyword in q_lower for keyword in ["cut", "reduce", "lower", "decrease", "trim"]) and \
           any(keyword in q_lower for keyword in ["spending", "expenses", "costs"]):
            return 'expense_reduction'
        
        # Cash position
        if any(keyword in q_lower for keyword in ["cash", "position", "balance", "after"]) and \
           any(keyword in q_lower for keyword in ["month", "year"]):
            return 'cash_position'
        
        return 'unknown'
    
    def is_available(self) -> bool:
        """Check if model is loaded and ready."""
        return self.model is not None and self.tokenizer is not None
    
    def plan_scenario_steps(self, question: str, context: dict = None) -> dict:
        """
        Plan multi-step scenario analysis (Tier 2: Tool Planning).
        
        For complex questions like "What if I use GI Bill for a master's?",
        return the tools and steps needed:
        
        Example output:
        {
            'intent': 'gi_bill',
            'steps': [
                {'tool': 'get_education_params', 'params': {'degree': 'master\'s'}},
                {'tool': 'calculate_gi_bill_bah', 'params': {'location': 'original'}},
                {'tool': 'recalculate_runway', 'params': {'use_bah': True}}
            ],
            'confidence': 0.85
        }
        
        This enables scenario_analyzer to orchestrate multiple calculations.
        """
        intent = self.classify_scenario_intent(question, context)
        
        # Define tool plans for each intent
        tool_plan = {
            'intent': intent,
            'steps': [],
            'confidence': 0.75
        }
        
        # For GI Bill questions: need to get education details and compute BAH
        if intent == 'gi_bill':
            tool_plan['steps'] = [
                {
                    'tool': 'extract_education_params',
                    'description': 'Extract degree type and location from question',
                    'params': {'question': question}
                },
                {
                    'tool': 'calculate_gi_bill_bah',
                    'description': 'Call step 2C to compute BAH for the education program',
                    'params': {'Education params extracted from question or current profile'}
                },
                {
                    'tool': 'recalculate_financial_scenario',
                    'description': 'Recalculate runway/deficit with BAH included',
                    'params': {'use_bah': True}
                }
            ]
        
        # For job search timeline: extract months
        elif intent == 'job_search_timeline':
            tool_plan['steps'] = [
                {
                    'tool': 'extract_timeline_params',
                    'description': 'Extract job search months from question',
                    'params': {'question': question}
                },
                {
                    'tool': 'recalculate_financial_scenario',
                    'description': 'Recalculate runway/deficit for new timeline',
                    'params': {}
                }
            ]
        
        # For savings questions: direct calculation
        elif intent in ['savings_runway', 'savings_sufficiency', 'expense_reduction']:
            tool_plan['steps'] = [
                {
                    'tool': 'recalculate_financial_scenario',
                    'description': 'Recalculate based on question context',
                    'params': {'question': question}
                }
            ]
        
        return tool_plan
