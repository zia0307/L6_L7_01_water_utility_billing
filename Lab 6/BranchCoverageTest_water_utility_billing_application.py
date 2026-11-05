"""
Lab 6 - Branch coverage tests for water_utility_billing.py

Goal: make every decision evaluate to both True and False (>= 90% branch coverage).
Includes everything from the code-coverage file plus the missing branches and
boundary values.

Run:
    coverage run --branch -m pytest BranchCoverageTest_water_utility_billing.py
    coverage report -m
"""
import pytest
from water_utility_billing import calculate_water_bill, check_meter_tampering


def make_account(usage_blocks, active=True, commercial=False, waiver=False):
    return {
        "is_active": active,
        "is_commercial": commercial,
        "has_leak_waiver": waiver,
        "usage_blocks": usage_blocks,
    }


# ---------- calculate_water_bill ----------

def test_single_active_residential():
    # 10 base + 30 * 1.5 = 55
    result = calculate_water_bill([make_account([30])], 10.0)
    assert result == {"total_billed": 55.0, "status": "NORMAL"}


def test_invalid_accounts_not_a_list():
    with pytest.raises(ValueError):
        calculate_water_bill("not a list", 10.0)


def test_inactive_account_is_skipped():
    result = calculate_water_bill([make_account([30], active=False)], 10.0)
    assert result["total_billed"] == 0.0
    assert result["status"] == "NO_ACTIVITY"


def test_non_positive_usage_is_flagged_and_skipped():
    # usage 0 and -5 add nothing, only the base fee remains
    result = calculate_water_bill([make_account([0, -5])], 10.0)
    assert result == {"total_billed": 10.0, "status": "NORMAL"}


def test_residential_high_usage_breaks_loop():
    # 10 + 120 * 4.5 = 550; the trailing block (30) is ignored because of break
    result = calculate_water_bill([make_account([120, 30])], 10.0)
    assert result["total_billed"] == 550.0


def test_commercial_high_usage_does_not_break_loop():
    # 10 + 120 * 3.5 + 30 * 1.5 = 475
    result = calculate_water_bill([make_account([120, 30], commercial=True)], 10.0)
    assert result["total_billed"] == 475.0


def test_medium_usage_tier():
    # 10 + 60 * 2.5 = 160
    result = calculate_water_bill([make_account([60])], 10.0)
    assert result["total_billed"] == 160.0


def test_leak_waiver_applied_when_total_above_200():
    # 10 + 120 * 4.5 = 550 -> waiver -50 = 500
    result = calculate_water_bill([make_account([120], waiver=True)], 10.0)
    assert result["total_billed"] == 500.0


def test_excessive_flags_status():
    # six non-positive blocks -> 6 flags (> 5)
    result = calculate_water_bill([make_account([0, 0, 0, 0, 0, 0])], 10.0)
    assert result["status"] == "EXCESSIVE_FLAGS"


def test_no_activity_status_empty_list():
    result = calculate_water_bill([], 10.0)
    assert result == {"total_billed": 0.0, "status": "NO_ACTIVITY"}


# ---------- check_meter_tampering ----------

def test_meter_no_data():
    assert check_meter_tampering([]) == "NO_DATA"


def test_meter_tamper_suspected():
    assert check_meter_tampering([[5, -1, -2]]) == "TAMPER_SUSPECTED"


def test_meter_clear():
    # a single backward reading followed by normal flow resets the counter
    assert check_meter_tampering([[5, -1, 3, 4]]) == "CLEAR"


# ---------- extra tests for branch coverage ----------

def test_invalid_negative_base_fee():
    with pytest.raises(ValueError):
        calculate_water_bill([make_account([30])], -1.0)


def test_leak_waiver_not_applied_when_total_at_or_below_200():
    # has_leak_waiver True but total (10 + 60 * 2.5 = 160) is not > 200 -> no deduction
    result = calculate_water_bill([make_account([60], waiver=True)], 10.0)
    assert result["total_billed"] == 160.0


def test_leak_waiver_boundary_exactly_200():
    # 50 + 60 * 2.5 = 200, and 200 is not > 200 -> no deduction
    result = calculate_water_bill([make_account([60], waiver=True)], 50.0)
    assert result["total_billed"] == 200.0


def test_boundary_usage_exactly_100_is_medium_tier():
    # 100 is not > 100, so it bills at 2.5: 0 + 100 * 2.5 = 250 and no flag
    result = calculate_water_bill([make_account([100])], 0.0)
    assert result == {"total_billed": 250.0, "status": "NORMAL"}


def test_boundary_usage_exactly_50_is_low_tier():
    # 50 is not > 50, so it bills at 1.5: 0 + 50 * 1.5 = 75
    result = calculate_water_bill([make_account([50])], 0.0)
    assert result["total_billed"] == 75.0


def test_boundary_usage_101_is_high_tier():
    result = calculate_water_bill([make_account([101])], 0.0)
    assert result["total_billed"] == 454.5


def test_exactly_five_flags_is_still_normal():
    result = calculate_water_bill([make_account([0, 0, 0, 0, 0])], 10.0)
    assert result["status"] == "NORMAL"


def test_no_activity_not_triggered_when_total_nonzero():
    result = calculate_water_bill([make_account([30])], 0.0)
    assert result["status"] == "NORMAL"


def test_no_activity_with_zero_base_fee_and_active_account():
    result = calculate_water_bill([make_account([])], 0.0)
    assert result == {"total_billed": 0.0, "status": "NO_ACTIVITY"}


def test_excessive_flags_takes_priority_over_no_activity():
    result = calculate_water_bill([make_account([0, 0, 0, 0, 0, 0])], 0.0)
    assert result["status"] == "EXCESSIVE_FLAGS"


def test_multiple_accounts_mixed_active_and_inactive():
    accounts = [
        make_account([30]),                       # 10 + 45 = 55
        make_account([30], active=False),         # skipped
        make_account([20], commercial=True),      # 10 + 30 = 40
    ]
    result = calculate_water_bill(accounts, 10.0)
    assert result == {"total_billed": 95.0, "status": "NORMAL"}


def test_missing_keys_use_defaults():
    # account without is_active is treated as inactive
    result = calculate_water_bill([{}], 10.0)
    assert result["status"] == "NO_ACTIVITY"


# ---------- extra meter tampering tests ----------

def test_meter_single_backward_reading_is_clear():
    assert check_meter_tampering([[5, -1]]) == "CLEAR"


def test_meter_non_consecutive_negatives_are_clear():
    assert check_meter_tampering([[-1, 2, -1, 3]]) == "CLEAR"


def test_meter_tamper_found_in_second_meter():
    assert check_meter_tampering([[1, 2, 3], [4, -1, -1]]) == "TAMPER_SUSPECTED"


def test_meter_empty_meter_list_is_clear():
    assert check_meter_tampering([[]]) == "CLEAR"


def test_meter_zero_delta_is_not_backward():
    assert check_meter_tampering([[-1, 0, -1]]) == "CLEAR"