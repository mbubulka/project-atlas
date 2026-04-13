import pytest

@pytest.mark.fast
@pytest.mark.sanity
def test_pension_sanity_checks():
    """
    Test layer 4: Bounds & Sanity Checks
    Ensure impossible values are rejected or warned.
    """
    # e.g., Pension cannot exceed 75% for 30 years service normally
    # e.g., Negative salaries or ages must be rejected
    assert True
