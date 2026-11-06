"""
run_tests.py - Test suite runner for LIFELINE Phase 1 Validator.

Verifies:
1. Valid test cases (valid_case_s.xlsx, valid_case_m.xlsx, valid_case_x.xlsx) PASS under --partial.
2. Every broken workbook in tests/ FAILS under --partial and flags the expected rule.
3. Prints a clean formatted table summarizing test results.
4. Exits with code 0 only if all test expectations are satisfied.
"""

import os
import sys
import subprocess
import glob

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
VALIDATOR_DIR = os.path.dirname(TESTS_DIR)
VALIDATE_PY = os.path.join(VALIDATOR_DIR, "validate.py")

# Expected broken rules map
EXPECTED_RULES = {
    "broken_s_01_pattern_count.xlsx": "V5",
    "broken_s_02_edit_bound.xlsx": "V5",
    "broken_s_03_disconnected_road.xlsx": "V4",
    "broken_s_04_wave_share_road.xlsx": "V4",
    "broken_s_05_duplicate_serial.xlsx": "V2",
    "broken_s_06_capacity_too_high.xlsx": "V2",
    "broken_s_07_target_is_hq.xlsx": "V2",
    "broken_s_08_cover_missing_edge.xlsx": "V6",
    "broken_s_09_violated_planted_3sat.xlsx": "V6",
    "broken_s_10_ration_sum_off.xlsx": "V6",
    "broken_s_11_wrong_claim.xlsx": "V5",
    "broken_s_12_float_in_int.xlsx": "V1",
    "broken_s_13_bad_header.xlsx": "V1",
    "broken_s_14_swapped_sheets.xlsx": "V1",
    "broken_s_15_v7_delta_penalty.xlsx": "V7",
    "broken_m_01_tour_missing_site.xlsx": "V3",
    "broken_m_02_repeated_switch_rule.xlsx": "V3",
    "broken_m_03_non_consecutive_crate_id.xlsx": "V3",
    "broken_m_04_alarm_tick_decreasing.xlsx": "V3",
    "broken_m_05_short_serial.xlsx": "V2",
    "broken_m_06_window_duration_invalid.xlsx": "V2",
    "broken_x_01_trap49_not_repeated.xlsx": "V8",
}


def run_validator(filepath):
    """Executes validate.py on filepath with --partial flag and returns (exit_code, stdout)."""
    cmd = [sys.executable, VALIDATE_PY, filepath, "--partial"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.returncode, res.stdout + res.stderr


def run_all_tests():
    print("=" * 80)
    print("RUNNING VALIDATOR TEST SUITE")
    print("=" * 80)

    all_passed = True

    # 1. Test Valid Workbooks
    valid_files = ["valid_case_s.xlsx", "valid_case_m.xlsx", "valid_case_x.xlsx"]
    print("\n--- 1. Testing Valid Single-Case Workbooks ---")
    for vf in valid_files:
        v_path = os.path.join(TESTS_DIR, vf)
        if not os.path.exists(v_path):
            print(f"ERROR: Missing valid test file: {vf}")
            all_passed = False
            continue
        code, out = run_validator(v_path)
        status = "PASS" if code == 0 else "FAIL"
        print(f"[{status}] {vf}: Exit Code {code}")
        if code != 0:
            all_passed = False
            print(f"      Output: {out.strip()}")

    # 2. Test Broken Workbooks
    print("\n--- 2. Testing Broken Workbooks Rejection Table ---")
    header = f"{'Broken Test File':<38} | {'Expected':<8} | {'Detected Rules':<16} | {'Rejected':<8} | {'Status'}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    broken_files = sorted(EXPECTED_RULES.keys())
    for bf in broken_files:
        b_path = os.path.join(TESTS_DIR, bf)
        if not os.path.exists(b_path):
            print(f"{bf:<38} | {EXPECTED_RULES[bf]:<8} | MISSING FILE    | NO       | FAIL")
            all_passed = False
            continue

        exp_rule = EXPECTED_RULES[bf]
        code, out = run_validator(b_path)
        rejected = (code != 0)

        # Detect which rules appear in the output
        detected = []
        for r_name in ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"]:
            if f"{r_name}:" in out or f"{r_name} GLOBAL:" in out:
                detected.append(r_name)

        detected_str = ",".join(detected) if detected else "None"
        rule_matched = exp_rule in detected
        test_ok = rejected and rule_matched

        if not test_ok:
            all_passed = False

        status_str = "PASS" if test_ok else "FAIL"
        rejected_str = "YES" if rejected else "NO"
        print(f"{bf:<38} | {exp_rule:<8} | {detected_str:<16} | {rejected_str:<8} | {status_str}")

    print("-" * len(header))
    print("\nTest Suite Summary:")
    print(f"Total Broken Copies Tested: {len(broken_files)}")
    print(f"Overall Test Result:        {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
