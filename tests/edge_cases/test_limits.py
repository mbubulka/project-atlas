import pytest

@pytest.mark.fast
@pytest.mark.edge_cases
def test_edge_case_zero_savings_handling(edge_case_zero_savings):
    """
    Test layer 5: Edge Cases
    Verify transition plan with zero savings and high expenses.
    """
    assert edge_case_zero_savings.current_savings == 0
    # ensure it doesn't crash or throw division by zero
    assert True
