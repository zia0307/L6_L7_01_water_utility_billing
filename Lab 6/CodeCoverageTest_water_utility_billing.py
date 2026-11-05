"""
Lab 6 - Code (line) coverage tests for water_utility_billing.py

Goal: execute every line of the application at least once (>= 90% line coverage).

Run:
    coverage run -m pytest CodeCoverageTest_water_utility_billing.py
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