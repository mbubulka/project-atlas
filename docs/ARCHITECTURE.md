# Architecture Overview

## System Design

Project Atlas implements a **hybrid Retrieval-Augmented Generation (RAG)** architecture optimized for military financial Q&A with explicit fairness considerations.

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ User Question: "What is the Survivor Benefit Plan?"                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ User Input      │
                    │ Validation      │
                    └────────┬────────┘
                             │
        ┌────────────────────▼────────────────────┐
        │                                         │
    ┌───▼────────┐                    ┌──────────▼────────┐
    │ FAISS      │                    │ Query             │
    │ Retriever  │                    │ Embedding         │
    │ (Dense)    │                    │ all-MiniLM-L6-v2  │
    └─────┬──────┘                    └──────────────────┘
          │
          │ k=10 candidates (similarity > 0.3)
          │
    ┌─────▼──────────────────────────┐
    │ Cross-Encoder Re-Ranker        │
    │ (ms-marco-MiniLM-L-6-v2)       │
    │ Threshold: 0.5                 │
    │ Output: Top-3 passages         │
    │ w/ relevance scores            │
    └─────┬──────────────────────────┘
          │
          │ Top-3 scored passages
          │
    ┌─────▼──────────────────────────┐
    │ FLAN-T5-Base Generator         │
    │ (250M parameters)              │
    │                                │
    │ Prompt: Question + Context     │
    │         + Relevance Scores     │
    └─────┬──────────────────────────┘
          │
    ┌─────▼──────────────────────┐
    │ Generated Answer           │
    │ (grounded in context)      │
    └─────┬──────────────────────┘
          │
    ┌─────▼──────────────────────┐
    │ Audit Logger               │
    │ SEC Rule 17a-4 Compliance  │
    │ (timestamp, user_id,       │
    │  question, passages,       │
    │  answer, confidence)       │
    └─────┬──────────────────────┘
          │
    ┌─────▼──────────────────────┐
    │ Answer to User             │
    │ + Passage Citations        │
    │ + Confidence Score         │
    └────────────────────────────┘
```

## Component Architecture

### 1. AI Layer (`src/ai_layer/`)

**FAISS Retriever** (`faiss_retriever.py`)
- **Purpose**: Dense passage retrieval
- **Model**: all-MiniLM-L6-v2 (384-dimensional embeddings)
- **Index**: FAISS Flat index over 561 military Q&A pairs
- **Hyperparameters**: k=10, similarity threshold > 0.3
- **Performance**: ~2-5ms retrieval latency

**Cross-Encoder Re-Ranker** (`cross_encoder.py`)
- **Purpose**: Semantic re-ranking for precision
- **Model**: ms-marco-MiniLM-L-6-v2 (pretrained on MS MARCO)
- **Input**: (question, passage) pairs
- **Output**: Relevance scores 0-1 per passage
- **Threshold**: 0.5 (passages below discarded)
- **Performance**: ~20-50ms for 3 passages

**Generator** (`generator.py`)
- **Purpose**: Generate grounded answer from top-3 passages
- **Model**: FLAN-T5-base (250M parameters, Google)
- **Task**: Abstractive summarization + reasoning
- **Input Format**: "Question: [Q] Context: [P1] [P2] [P3] Answer:"
- **Performance**: ~500-800ms per query
- **Grounding Rate**: 95% of answers traced to retrieved passages

**Audit Logger** (`audit_logger.py`)
- **Purpose**: SEC Rule 17a-4 compliant audit trail
- **Log Fields**: timestamp, user_id, question, passages, scores, answer, confidence
- **Retention**: 3 years (configurable)
- **Immutability**: Hash chains prevent tampering
- **Access Control**: Role-based (e.g., financial counselors only)

### 2. Data Layer (`src/data_layer/`)

**Loader** (`loader.py`)
- **Purpose**: Ingest and validate user data
- **Supported Formats**: CSV (budget records), JSON (profiles)
- **Cleaning**: Currency formatting, date parsing, numeric validation
- **Error Handling**: Graceful degradation with user feedback

**Knowledge Base** (`data/military_qa_pairs.json`)
- **Size**: 561 Q&A pairs (144 canonical + 417 paraphrased)
- **Coverage**: 7 benefit categories
  - Pension Computation (15%)
  - Healthcare / TRICARE (20%)
  - Survivor Benefits (14%)
  - VA Loans / Housing (12%)
  - Taxation (10%)
  - Special Pays (8%)
  - Integration Scenarios (21%)
- **Source**: DFAS, VA.gov, TRiCARE official documentation
- **Update Frequency**: Quarterly (policy changes, benefits updates)

### 3. Model Layer (`src/model_layer/`)

**Financial Calculators**
- Pension computation (High-36, multipli­er, vesting rules)
- Tax modeling (Federal, state, FICA with military-specific rules)
- Healthcare cost projections (TRICARE, VA, ACA premium estimation)
- Survivor Benefit Plan (SBP) calculations
- VA disability offsets and interaction rules

### 4. UI Layer (`src/ui_layer/`)

**Streamlit Dashboard** (`dashboard.py`)
- Month-by-month cash flow visualization
- Interactive scenario comparison
- Benchmark against similar profiles
- Risk alerts (cash flow warnings, benefit discontinuities)

## Fairness & Bias Mitigation

### Weak-Category Amplification

**Problem**: Imbalanced dataset → poor performance on rare categories

**Solution**: 3.0× targeted oversampling with paraphrase diversity

```
Original Training Data:
- Housing: 7 examples → 62 (9×)
- Survivor: 8 examples → 21 (3×)
- Taxation: 10 examples → 28 (3×)

Result:
- Housing: +54% ROUGE-L improvement
- Survivor: +46.6% improvement
- Taxation: +43.9% improvement
```

### What-If Consistency Testing

**Metric**: Rephrasing the same question → measure variance in answers

```
Variant Consistency: Textual alignment across phrasings
Reasoning Consistency: Logical reasoning alignment
Overall Consistency: Aggregate fairness across domains

Target: ≥60%
Achieved: 67% ± 8%
```

**Performance by Domain**:
- Factual queries: 88% consistency (e.g., "What is the VA funding fee?")
- Complex reasoning: 54% consistency (multi-factor scenarios)
- Healthcare rules: 85% consistency
- Tax calculations: 65% consistency

### Differential Performance

Track ROUGE-L, BLEU, Entity F1 per benefit category to detect disparities.

## Data Flow

### Initialization

1. **Load FAISS Index**: 561-pair military KB with embeddings
2. **Initialize Models**: 
   - all-MiniLM-L6-v2 (embeddings)
   - ms-marco-MiniLM-L-6-v2 (cross-encoder)
   - FLAN-T5-base (generator)
3. **Setup Audit Logger**: Initialize log file, verify retention policy
4. **Ready**: System ready for queries

### Query Processing

1. **Embed Query**: all-MiniLM-L6-v2 → 384-dim vector
2. **Retrieve**: FAISS similarity search → top 10 passages
3. **Re-rank**: Cross-encoder scores passages → keep top 3 (score > 0.5)
4. **Generate**: FLAN-T5 + top-3 passages → answer
5. **Log**: Record timestamp, question, passages, scores, answer, confidence
6. **Return**: Answer + passage citations + confidence to user

### Performance Profile

| Component | Latency | Throughput |
|-----------|---------|-----------|
| Embedding | 1-2ms | All queries atomic |
| Retrieval (FAISS) | 2-5ms | ~200 QPS single machine |
| Re-ranking | 20-50ms | ~20 QPS for top-3 |
| Generation | 500-800ms | 1-2 QPS |
| Audit Logging | <1ms | Async post-generation |
| **Total** | ~1200ms | 0.8 QPS end-to-end |

**Deployment Note**: 1.2 sec latency acceptable for asynchronous APIs (web services, chatbots). Real-time applications can optimize via:
- Approximate NN search (IVF_FLAT) → <1ms retrieval
- Model quantization → 4× speedup
- Model distillation → FLAN-T5-small + retrieval

## Compliance & Governance

### NIST AI Risk Management Framework (NIST AI RMF 1.0)

**GOVERN** (Oversight & Accountability)
- Clear ownership: Michael Bubulka (author)
- Audit logging per SEC Rule 17a-4
- Version control of model updates
- Access control documentation

**MAP** (Understanding & Context)
- Purpose: Educational financial guidance for military separatees
- Intended Users: Transitioning service members, military financial counselors
- Known Limitations: 67% What-If consistency (complex reasoning ≤54%)
- Scope: Military-specific Q&A only; not financial advice

**MEASURE** (Evaluation & Testing)
- Performance metrics: ROUGE-L 0.3966 (+371% improvement)
- Fairness metrics: Differential ROUGE-L by category, What-If consistency 67% ± 8%
- Bias detection: 7-category fairness reporting
- Baseline: FLAN-T5-small fine-tuning alone (ROUGE-L 0.0854)

**MANAGE** (Mitigation & Monitoring)
- Hallucination mitigation: 95% retrieval grounding
- Fairness audits: Biannual category performance review
- Transparency: Users see retrieved passages + relevance scores
- Documentation: Comprehensive disclosure of limitations

### SEC Rule 17a-4 Compliance

- ✅ Immutable audit records (hash-chained)
- ✅ 3-year retention policy (configurable)
- ✅ Timestamped entries
- ✅ Complete record of inference history
- ✅ Access control (role-based)
- ✅ Deletion/modification prevention

## Testing Strategy

### Unit Tests (`tests/test_*.py`)
- Component functionality (retriever, ranker, generator)
- Data validation and cleaning
- Calculation correctness

### Integration Tests
- End-to-end RAG pipeline
- Fairness metric evaluation
- Audit logging integrity

### Fairness Tests
- What-If consistency across domains
- Differential performance by category
- Bias detection (subgroup analysis)

### Regression Tests
- Baseline performance maintained (ROUGE-L > 0.35)
- Latency within bounds (<1.5s)
- Audit logs valid and complete

## Development Workflow

1. **Feature Branch**: Feature develops on `feature/xyz`
2. **Testing**: Full test suite passes (`pytest tests/ -v --cov=src/`)
3. **Code Review**: Peer review of fairness & compliance implications
4. **Merges**: Approved features merge to `main`
5. **Versioning**: Semantic versioning (MAJOR.MINOR.PATCH)
6. **Releases**: Tagged releases with changelog documentation

## Future Enhancements

**Short-term** (next quarter):
- Multi-turn conversation memory (context between Q&A pairs)
- Fine-tuning on domain-specific financial language
- Latency optimization (model quantization, distillation)

**Medium-term** (next 2 quarters):
- Hierarchical Q&A for complex multi-factor reasoning
- Synthetic data generation for even rarer categories
- Explainability module (SHAP/LIME) for answer reasoning

**Long-term** (research directions):
- Retriever fine-tuning with domain ranking signals
- End-to-end differentiable ranking (learned retrieval)
- Cross-domain transfer learning (other vulnerable populations)
