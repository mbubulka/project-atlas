#!/usr/bin/env python
"""
Diagnostic: Which AI systems are being used in ProjectAtlas?

Checks:
1. Milestone E RAG availability + file status
2. Milestone C FLAN-T5 availability + model loading
3. Scenario Analyzer initialization
4. Hybrid routing verification
"""

import sys
from pathlib import Path

print("\n" + "="*70)
print("AI SYSTEM DIAGNOSTIC: Milestone C vs E Verification")
print("="*70 + "\n")

# 1. Check Milestone E RAG FILES
print("1️⃣  MILESTONE E RAG FILES:")
print("-" * 70)
data_dir = Path('d:\\Project Atlas\\data')
rag_files = [
    'milestone_e_knowledge_base.json',
    'milestone_e_faiss_index.pkl',
    'milestone_e_kb_embeddings.npz',
    'milestone_e_production_config.json',
]

rag_files_ok = True
for fname in rag_files:
    fpath = data_dir / fname
    if fpath.exists():
        print(f"   ✅ {fname}")
    else:
        print(f"   ❌ {fname} - MISSING")
        rag_files_ok = False

print(f"\nRAG Files Status: {'✅ COMPLETE' if rag_files_ok else '❌ INCOMPLETE'}\n")


# 2. Check Milestone C FLAN Models
print("2️⃣  MILESTONE C FLAN-T5 MODELS:")
print("-" * 70)
milestone_c_dir = Path('d:\\personal2\\Milestone_C')  # Original location
project_c_dir = Path('d:\\Project Atlas\\models')  # Possibly copied location

flan_models = [
    'flan_t5_fold1_best.pt',
    'flan_t5_fold1_final_trained.pt',
    'flan_t5_fold1_phase3_retrained.pt',
]

flan_found = False
for fname in flan_models:
    # Check original location
    orig = milestone_c_dir / fname
    if orig.exists():
        print(f"   ✅ Found at: {orig}")
        flan_found = True
        continue
    
    # Check project location
    proj = project_c_dir / fname
    if proj.exists():
        print(f"   ✅ Found at: {proj}")
        flan_found = True
        continue
    
    print(f"   ⚠️  {fname} - Not found in standard locations")

print(f"\nFLAN-T5 Models Status: {'✅ FOUND' if flan_found else '⚠️  Check paths'}\n")


# 3. Check scenario_analyzer imports
print("3️⃣  SCENARIO ANALYZER INITIALIZATION:")
print("-" * 70)

try:
    from src.ai_layer import scenario_analyzer
    
    # Check what's imported
    RAG_AVAILABLE = scenario_analyzer.RAG_AVAILABLE
    FLAN_AVAILABLE = scenario_analyzer.FLAN_T5_AVAILABLE
    
    print(f"   RAGFinancialAdvisor import: {'✅ Available' if RAG_AVAILABLE else '❌ Not available'}")
    print(f"   FlanT5Loader import: {'✅ Available' if FLAN_AVAILABLE else '❌ Not available'}")
    
    # Try to initialize
    print("\n   Initializing ScenarioAnalyzer...")
    analyzer = scenario_analyzer.ScenarioAnalyzer()
    
    print(f"   RAG Advisor status: {'✅ Loaded' if analyzer.rag_advisor else '❌ Not loaded'}")
    print(f"   FLAN-T5 status: {'✅ Loaded' if analyzer.flan_t5 else '❌ Not loaded'}")
    
    if analyzer.rag_advisor:
        print(f"      → RAG is available for factual Q&A questions")
    if analyzer.flan_t5:
        print(f"      → FLAN-T5 is available for scenario intent detection")
    
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("SUMMARY:")
print("="*70)
print("""
HYBRID AI SYSTEM ARCHITECTURE:
  
  ✅ Milestone E RAG (Primary)
     → Factual Q&A: "What is TRICARe Prime?"
     → Knowledge Base: 561 Q&A pairs
     → Confidence threshold: 0.7
     → If available AND confident → Use RAG answer
  
  ✅ Milestone C FLAN-T5 (Fallback)
     → Scenario analysis: "What if take 9 months?"
     → Intent detection: Detects scenario type
     → Parameter extraction: Parses numbers from questions
     → Financial calculations: Generates recommendations
     → If RAG unavailable OR low confidence → Use FLAN-T5

STATUS INTERPRETATION:
  - If both available: Questions routed to RAG first, fallback to FLAN-T5
  - If only RAG: Factual Q&A works, scenario analysis uses keyword matching
  - If only FLAN-T5: All scenarios use FLAN-T5 intent detection
  - If neither: Keyword-based fallback only (not recommended)
""")
print("="*70 + "\n")
