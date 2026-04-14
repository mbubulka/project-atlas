# Developer Quick Reference: Sample Budget Auto-Generation

## Location in Codebase
- **Main implementation**: `src/ui_layer/wizard_simplified.py`
- **Function**: `generate_sample_budget(profile_name)` (lines ~1500-1590)
- **Integration**: `render_step_6_classification()` (lines ~1595-1640)

## Key Components

### generate_sample_budget() Function
```python
def generate_sample_budget(profile_name):
    """Generate sample budget transactions based on demo profile demographics."""
    # Returns: pandas.DataFrame with Date, Description, Amount columns
    # Input: One of 4 profile names:
    #   - "E-5 Single +1"
    #   - "E-6 Married"
    #   - "O-3 Married +2"
    #   - "E-9 Single"
```

**What it does:**
1. Define realistic budget templates for each military household type
2. Generate 3 months of transactions (current month + 2 previous)
3. Vary amounts by ±20% for realism
4. Split monthly categories into multiple transactions
5. Return pandas DataFrame ready for display

### Auto-Detection in Step 8
When Step 8 renders:
```python
demo_loaded = st.session_state.get("_demo_profile_loaded", False)
demo_profile_name = st.session_state.get("_demo_profile_name", None)

if demo_loaded and demo_profile_name:
    sample_df = generate_sample_budget(demo_profile_name)
    if sample_df is not None:
        st.session_state.expense_transactions = sample_df
```

## Testing Instructions

### Quick Test
```bash
cd d:\Project Atlas
python test_sample_budget.py
```

Expected output:
- 4 test profiles
- Transaction count for each (~80-100 transactions)
- Date range (3 months)
- Category breakdown
- Average monthly expense

### End-to-End Test
1. Run the app: `streamlit run app.py`
2. Go to Step 1
3. Click any demo profile button (e.g., "E-5 Single +1")
4. Click "Next →" repeatedly to advance
5. At Step 8, verify:
   - "Auto-Generated Sample Budget" section appears
   - Profile name displayed correctly
   - ✅ Green success message shows transaction count
   - Preview shows realistic transactions
   - Categories match expected profile

### Manual Code Review

**Profile names must match exactly:**
```python
DEMO_PROFILES = {
    "E-5 Single +1": {...},      # Must match key in generate_sample_budget
    "E-6 Married": {...},
    "O-3 Married +2": {...},
    "E-9 Single": {...},
}
```

**Budget templates in generate_sample_budget:**
```python
budget_templates = {
    "E-5 Single +1": { ... },    # Must match DEMO_PROFILES keys
    "E-6 Married": { ... },
    "O-3 Married +2": { ... },
    "E-9 Single": { ... },
}
```

## Session State Variables

**Set by load_demo_profile() in Step 1:**
- `_demo_profile_loaded`: Boolean (True if demo loaded)
- `_demo_profile_name`: String (profile name)
- Plus ~40 profile-specific financial fields

**Used in render_step_6_classification() for Step 8:**
```python
demo_loaded = st.session_state.get("_demo_profile_loaded", False)
demo_profile_name = st.session_state.get("_demo_profile_name", None)
```

**Set by Step 8 after generation:**
- `expense_transactions`: DataFrame with generated transactions

## Data Flow

```
Step 1: Load Demo Profile
  ↓
Sets: _demo_profile_loaded=True, _demo_profile_name="E-5 Single +1"
  ↓
  ... User clicks through steps 2-7 ...
  ↓
Step 8: Render Income & Expense Classification
  ↓
Detects: demo_loaded=True, demo_profile_name="E-5 Single +1"
  ↓
Calls: generate_sample_budget("E-5 Single +1")
  ↓
Returns: DataFrame with 80-100 transactions
  ↓
Sets: st.session_state.expense_transactions = df
  ↓
Displays: Success message, preview, classification UI
  ↓
User can: Edit, classify, or upload own data to override
```

## Troubleshooting

### "Could not generate sample budget for profile X"
- Check DEMO_PROFILES keys in Step 1
- Verify generate_sample_budget() has matching key in budget_templates
- Ensure profile name is exactly matching (case-sensitive)

### DataFrame not showing
- Verify pandas import in wizard_simplified.py
- Check that generate_sample_budget() returns valid DataFrame
- Test: `python test_sample_budget.py`

### Session state issue
- Verify _demo_profile_loaded is set to True
- Check _demo_profile_name is not None
- Add debug prints in Step 8: `st.write(f"Debug: {demo_loaded}, {demo_profile_name}")`

### Missing transactions
- Check random.randint(2, 4) in generate_sample_budget
- Verify date range calculation (30 * month_offset)
- Test individual profile: Run test_sample_budget.py

## Performance Notes

- Generate_sample_budget() runs on every Step 8 render
- Small overhead: ~50-100ms for 3 profiles × 10 categories
- No external API calls or I/O
- Caching: Could be added if performance issues arise

## Future Enhancements

Ideas for improvement:
1. Add seasonal spending variation (higher in summer/holidays)
2. Include recurring payments (insurance, subscriptions)
3. Add debt service (car loans, student loans)
4. Generate more realistic descriptions from templates
5. Add spending trend analysis (increasing/decreasing over time)
6. Export sample budget to CSV
7. Save generated budget for future sessions

## Related Files

- `SAMPLE_BUDGET_AUTO_GENERATION.md` - User documentation
- `test_sample_budget.py` - Test script
- `src/data_layer/loader.py` - CSV parsing (clean_transaction_csv)
- `src/ui_layer/classification_adjuster.py` - Expense classification UI

---

**Last Updated**: 2025-01-10
**Status**: Complete and tested ✅
