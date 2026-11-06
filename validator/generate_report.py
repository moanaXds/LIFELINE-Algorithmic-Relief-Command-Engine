"""
generate_report.py - Single command script to validate cases.xlsx, run broken tests,
and generate the comprehensive validation_report.txt.

Usage:
    python validator/generate_report.py
"""

import os
import sys
import subprocess

VALIDATOR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(VALIDATOR_DIR)
CASES_XLSX = os.path.join(PROJECT_ROOT, "cases.xlsx")
REPORT_TXT = os.path.join(PROJECT_ROOT, "validation_report.txt")
VALIDATE_PY = os.path.join(VALIDATOR_DIR, "validate.py")
RUN_TESTS_PY = os.path.join(VALIDATOR_DIR, "tests", "run_tests.py")


def main():
    print("Generating complete validation_report.txt...")
    report_lines = []

    report_lines.append("=" * 80)
    report_lines.append("DAA PROJECT 'LIFELINE' PHASE 1 - MASTER VALIDATION REPORT")
    report_lines.append("Group Seed: 18 | Target Dataset: cases.xlsx (50 Cases: 18-00 to 18-49)")
    report_lines.append("=" * 80)
    report_lines.append("")

    # 1. Run Master Dataset Validation
    report_lines.append("SECTION 1: 50-CASE BENCHMARK VALIDATION (cases.xlsx)")
    report_lines.append("-" * 80)
    
    cmd_cases = [sys.executable, VALIDATE_PY, CASES_XLSX]
    res_cases = subprocess.run(cmd_cases, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    report_lines.append(res_cases.stdout.strip())
    report_lines.append("")

    # 2. Run Broken Copies Test Suite
    report_lines.append("=" * 80)
    report_lines.append("SECTION 2: NEGATIVE TESTING & BROKEN COPIES REJECTION")
    report_lines.append("-" * 80)

    cmd_tests = [sys.executable, RUN_TESTS_PY]
    res_tests = subprocess.run(cmd_tests, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    report_lines.append(res_tests.stdout.strip())
    report_lines.append("")

    # 3. Final Verdict
    report_lines.append("=" * 80)
    report_lines.append("FINAL VERDICT:")
    if res_cases.returncode == 0 and res_tests.returncode == 0:
        report_lines.append("STATUS: ALL CHECKS PASSED (50/50 CASES VALIDATED + ALL BROKEN COPIES REJECTED)")
    else:
        report_lines.append("STATUS: VALIDATION OR TEST FAILURES DETECTED")
    report_lines.append("=" * 80)

    full_report = "\n".join(report_lines)
    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(full_report)

    # Also write a copy inside validator/ for convenience
    with open(os.path.join(VALIDATOR_DIR, "validation_report.txt"), "w", encoding="utf-8") as f:
        f.write(full_report)

    print(f"Report written successfully to {REPORT_TXT}")
    print(f"Final exit status: {res_cases.returncode or res_tests.returncode}")
    return res_cases.returncode or res_tests.returncode


if __name__ == "__main__":
    sys.exit(main())

