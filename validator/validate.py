"""
validate.py - Main CLI entry point for DAA Project 'LIFELINE' Phase 1 Validator.

Usage:
    python validate.py <path_to_cases.xlsx> [--partial]

Output Format:
    Per case:
        "18-00: PASS"
    or
        "18-00: FAIL"
            "V1: ..."
            "V2: ..."
    Then:
        GLOBAL:
            "V1 GLOBAL: ..." (or "GLOBAL: PASS")
        SUMMARY:
            Cases: 50 | Passed: 50 | Failed: 0
    Exit code: 0 on success, 1 on failure.
"""

import sys
import argparse
import os

from load import load_dataset
from v1_structure import validate_case_v1, validate_global_v1
from v2_ranges import validate_case_v2
from v3_ids import validate_case_v3
from v4_graph import validate_case_v4
from v5_text_claims import validate_case_v5
from v6_planted import validate_case_v6
from v7_signatures import validate_case_v7, validate_global_variety

# Optional import for Stage 5 (V8 traps)
try:
    from v8_traps import validate_case_v8
except ImportError:
    def validate_case_v8(case_id, case_data): return []


def run_validation(filepath, partial=False):
    """
    Executes the full suite of validation checks on the provided workbook.
    """
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading dataset from '{filepath}' (partial={partial})...")
    global_errors, case_records, case_order, case_load_errors = load_dataset(filepath)

    case_results = {}
    total_passed = 0
    total_failed = 0

    # Validate each case in order
    for cid in case_order:
        c_errors = []
        c_data = case_records.get(cid, {})

        # Load-time cell/type errors
        if cid in case_load_errors:
            c_errors.extend(case_load_errors[cid])

        # Stage V1: Structure & Schema
        c_errors.extend(validate_case_v1(cid, c_data))

        # Stage V2: Sizes & Ranges
        c_errors.extend(validate_case_v2(cid, c_data))

        # Stage V3: Identifiers & Cross-references
        c_errors.extend(validate_case_v3(cid, c_data))

        # Stage V4: Graph Connectivity & Waves
        c_errors.extend(validate_case_v4(cid, c_data))

        # Stage V5: Text, Patterns, Reports & Claims
        c_errors.extend(validate_case_v5(cid, c_data))

        # Stage V6: Planted Objects
        c_errors.extend(validate_case_v6(cid, c_data))

        # Stage V7: Disaster Signatures
        c_errors.extend(validate_case_v7(cid, c_data))

        # Stage V8: Hostile Traps
        c_errors.extend(validate_case_v8(cid, c_data))

        case_results[cid] = c_errors
        if not c_errors:
            print(f"{cid}: PASS")
            total_passed += 1
        else:
            print(f"{cid}: FAIL")
            for err in c_errors:
                print(f"    {err}")
            total_failed += 1

    # Global Validation
    global_all_errors = list(global_errors)
    global_all_errors.extend(validate_global_v1(case_order, partial=partial))
    global_all_errors.extend(validate_global_variety(case_records, partial=partial))

    print("\n" + "=" * 50)
    print("GLOBAL CHECKS:")
    print("=" * 50)
    if not global_all_errors:
        print("GLOBAL: PASS")
    else:
        for g_err in global_all_errors:
            print(f"    {g_err}")

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Cases Evaluated: {len(case_order)}")
    print(f"Cases Passed:    {total_passed}")
    print(f"Cases Failed:    {total_failed}")
    print(f"Global Status:   {'PASS' if not global_all_errors else 'FAIL'}")
    print("=" * 50)

    if total_failed == 0 and len(global_all_errors) == 0:
        return 0
    else:
        return 1


def main():
    parser = argparse.ArgumentParser(description="LIFELINE Phase 1 Dataset Validator")
    parser.add_argument("workbook", help="Path to cases.xlsx")
    parser.add_argument(
        "--partial",
        action="store_true",
        help="Skip global checks (50-case count, variety, cross-case uniqueness) for small test files"
    )
    args = parser.parse_args()

    exit_code = run_validation(args.workbook, partial=args.partial)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
