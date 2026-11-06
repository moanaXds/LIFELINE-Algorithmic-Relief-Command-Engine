"""
make_broken.py - Generates systematically corrupted workbooks for testing the LIFELINE Phase 1 Validator.

Generates broken copies from valid_case_s.xlsx, valid_case_m.xlsx, and valid_case_x.xlsx,
targeting specific rules across all validator stages:
- V1: Swapped sheet order, bad header name, float in integer column.
- V2: Duplicate serial, short serial, capacity > 70%, target is HQ, window duration < 5.
- V3: Non-consecutive IDs, tour not a permutation, repeated switch in a safety rule, decreasing alarm tick.
- V4: Disconnected graph, closure waves sharing a road.
- V5: Pattern count mismatch, edit_bound too small, optimal claim mismatch.
- V6: Planted cover missing an edge, violated planted 3-SAT assignment, ration sum mismatch.
- V7: Scenario 1 (Delta Flood) penalties < 40%.
- V8: Trap 49 (Near-miss trap) log repetition < 90%.
"""

import os
import shutil
import openpyxl

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_S = os.path.join(TESTS_DIR, "valid_case_s.xlsx")
VALID_M = os.path.join(TESTS_DIR, "valid_case_m.xlsx")
VALID_X = os.path.join(TESTS_DIR, "valid_case_x.xlsx")


def modify_workbook(src_path, dst_path, modifier_fn):
    """Loads a workbook, applies modifier_fn(wb), and saves to dst_path."""
    wb = openpyxl.load_workbook(src_path)
    modifier_fn(wb)
    wb.save(dst_path)
    wb.close()


def generate_broken_cases():
    print(f"Generating broken workbooks in {TESTS_DIR}...")
    broken_manifest = {}

    # -------------------------------------------------------------
    # 1. Broken copies from valid_case_s.xlsx
    # -------------------------------------------------------------

    # Broken S-01: V5 pattern count mismatch
    def mod_s01(wb):
        ws = wb['radio_patterns']
        ws.cell(2, 4, 999)  # row 2, col 4 is count of pattern 0
    f = os.path.join(TESTS_DIR, "broken_s_01_pattern_count.xlsx")
    modify_workbook(VALID_S, f, mod_s01)
    broken_manifest[f] = "V5"

    # Broken S-02: V5 edit_bound too small
    def mod_s02(wb):
        ws = wb['cases']
        ws.cell(2, 10, 1)  # col 10 is edit_bound
    f = os.path.join(TESTS_DIR, "broken_s_02_edit_bound.xlsx")
    modify_workbook(VALID_S, f, mod_s02)
    broken_manifest[f] = "V5"

    # Broken S-03: V4 graph disconnected
    def mod_s03(wb):
        ws = wb['roads']
        rows_to_keep = [ws.cell(1, c).value for c in range(1, 7)]
        valid_rows = []
        for r in range(2, ws.max_row + 1):
            u = ws.cell(r, 3).value
            v = ws.cell(r, 4).value
            if u != 1 and v != 1:
                valid_rows.append([ws.cell(r, c).value for c in range(1, 7)])
        wb.remove(ws)
        ws_new = wb.create_sheet(title='roads', index=3)
        ws_new.append(rows_to_keep)
        for idx, row in enumerate(valid_rows):
            row[1] = idx
            ws_new.append(row)
    f = os.path.join(TESTS_DIR, "broken_s_03_disconnected_road.xlsx")
    modify_workbook(VALID_S, f, mod_s03)
    broken_manifest[f] = "V4"

    # Broken S-04: V4 waves sharing a road
    def mod_s04(wb):
        ws = wb['waves']
        ws.cell(3, 3, ws.cell(2, 3).value)
    f = os.path.join(TESTS_DIR, "broken_s_04_wave_share_road.xlsx")
    modify_workbook(VALID_S, f, mod_s04)
    broken_manifest[f] = "V4"

    # Broken S-05: V2 duplicate serial
    def mod_s05(wb):
        ws = wb['crates']
        ws.cell(3, 7, ws.cell(2, 7).value)
    f = os.path.join(TESTS_DIR, "broken_s_05_duplicate_serial.xlsx")
    modify_workbook(VALID_S, f, mod_s05)
    broken_manifest[f] = "V2"

    # Broken S-06: V2 capacity too high (> 70% of total crate weight)
    def mod_s06(wb):
        ws = wb['cases']
        ws.cell(2, 6, 9999)
    f = os.path.join(TESTS_DIR, "broken_s_06_capacity_too_high.xlsx")
    modify_workbook(VALID_S, f, mod_s06)
    broken_manifest[f] = "V2"

    # Broken S-07: V2 target is HQ (location 0)
    def mod_s07(wb):
        ws = wb['cases']
        ws.cell(2, 7, 0)
    f = os.path.join(TESTS_DIR, "broken_s_07_target_is_hq.xlsx")
    modify_workbook(VALID_S, f, mod_s07)
    broken_manifest[f] = "V2"

    # Broken S-08: V6 cover missing an edge
    def mod_s08(wb):
        ws = wb['sensor_cover']
        ws.cell(2, 2, 999)
    f = os.path.join(TESTS_DIR, "broken_s_08_cover_missing_edge.xlsx")
    modify_workbook(VALID_S, f, mod_s08)
    broken_manifest[f] = "V6"

    # Broken S-09: V6 violated planted 3-SAT assignment
    def mod_s09(wb):
        ws = wb['safety_planted']
        val = ws.cell(2, 3).value
        ws.cell(2, 3, 1 - val)
    f = os.path.join(TESTS_DIR, "broken_s_09_violated_planted_3sat.xlsx")
    modify_workbook(VALID_S, f, mod_s09)
    broken_manifest[f] = "V6"

    # Broken S-10: V6 ration sum off
    def mod_s10(wb):
        ws = wb['cases']
        ws.cell(2, 15, ws.cell(2, 15).value + 77)
    f = os.path.join(TESTS_DIR, "broken_s_10_ration_sum_off.xlsx")
    modify_workbook(VALID_S, f, mod_s10)
    broken_manifest[f] = "V6"

    # Broken S-11: V5 wrong claim (cargo_opt)
    def mod_s11(wb):
        ws = wb['claims']
        ws.cell(2, 2, ws.cell(2, 2).value + 50)
    f = os.path.join(TESTS_DIR, "broken_s_11_wrong_claim.xlsx")
    modify_workbook(VALID_S, f, mod_s11)
    broken_manifest[f] = "V5"

    # Broken S-12: V1 float in integer column
    def mod_s12(wb):
        ws = wb['crates']
        ws.cell(2, 4, 15.5)
    f = os.path.join(TESTS_DIR, "broken_s_12_float_in_int.xlsx")
    modify_workbook(VALID_S, f, mod_s12)
    broken_manifest[f] = "V1"

    # Broken S-13: V1 bad header name
    def mod_s13(wb):
        ws = wb['crates']
        ws.cell(1, 7, "wrong_serial_header")
    f = os.path.join(TESTS_DIR, "broken_s_13_bad_header.xlsx")
    modify_workbook(VALID_S, f, mod_s13)
    broken_manifest[f] = "V1"

    # Broken S-14: V1 swapped sheet order
    def mod_s14(wb):
        wb._sheets[1], wb._sheets[2] = wb._sheets[2], wb._sheets[1]
    f = os.path.join(TESTS_DIR, "broken_s_14_swapped_sheets.xlsx")
    modify_workbook(VALID_S, f, mod_s14)
    broken_manifest[f] = "V1"

    # Broken S-15: V7 Scenario 1 (Delta Flood) penalty < 40%
    def mod_s15(wb):
        ws = wb['locations']
        for r in range(2, ws.max_row + 1):
            ws.cell(r, 4, 0)  # zero out all penalties
    f = os.path.join(TESTS_DIR, "broken_s_15_v7_delta_penalty.xlsx")
    modify_workbook(VALID_S, f, mod_s15)
    broken_manifest[f] = "V7"

    # -------------------------------------------------------------
    # 2. Broken copies from valid_case_m.xlsx
    # -------------------------------------------------------------

    # Broken M-01: V3 tour missing a site (visits site 1 twice)
    def mod_m01(wb):
        ws = wb['tour']
        ws.cell(3, 3, ws.cell(2, 3).value)
    f = os.path.join(TESTS_DIR, "broken_m_01_tour_missing_site.xlsx")
    modify_workbook(VALID_M, f, mod_m01)
    broken_manifest[f] = "V3"

    # Broken M-02: V3 repeated switch in a rule
    def mod_m02(wb):
        ws = wb['safety_rules']
        lit1 = ws.cell(2, 3).value
        ws.cell(2, 4, -abs(lit1))
    f = os.path.join(TESTS_DIR, "broken_m_02_repeated_switch_rule.xlsx")
    modify_workbook(VALID_M, f, mod_m02)
    broken_manifest[f] = "V3"

    # Broken M-03: V3 non-consecutive crate_id
    def mod_m03(wb):
        ws = wb['crates']
        ws.cell(3, 2, 99)
    f = os.path.join(TESTS_DIR, "broken_m_03_non_consecutive_crate_id.xlsx")
    modify_workbook(VALID_M, f, mod_m03)
    broken_manifest[f] = "V3"

    # Broken M-04: V3 decreasing alarm tick
    def mod_m04(wb):
        ws = wb['incidents']
        ws.cell(3, 3, ws.cell(2, 3).value - 1)
    f = os.path.join(TESTS_DIR, "broken_m_04_alarm_tick_decreasing.xlsx")
    modify_workbook(VALID_M, f, mod_m04)
    broken_manifest[f] = "V3"

    # Broken M-05: V2 short serial (7-digit)
    def mod_m05(wb):
        ws = wb['crates']
        ws.cell(2, 7, 9999999)
    f = os.path.join(TESTS_DIR, "broken_m_05_short_serial.xlsx")
    modify_workbook(VALID_M, f, mod_m05)
    broken_manifest[f] = "V2"

    # Broken M-06: V2 window duration < 5 minutes
    def mod_m06(wb):
        ws = wb['windows']
        s = ws.cell(2, 3).value
        ws.cell(2, 4, s + 2)
    f = os.path.join(TESTS_DIR, "broken_m_06_window_duration_invalid.xlsx")
    modify_workbook(VALID_M, f, mod_m06)
    broken_manifest[f] = "V2"

    # -------------------------------------------------------------
    # 3. Broken copy from valid_case_x.xlsx (Case 18-49)
    # -------------------------------------------------------------

    # Broken X-01: V8 Trap 49 log is NOT 90% repeated
    def mod_x01(wb):
        ws = wb['radio_log']
        # Replace the log text with random non-repeated sequence
        import random, string
        symbols = list(string.ascii_uppercase + string.digits + '_-')
        for r in range(2, ws.max_row + 1):
            cur_txt = ws.cell(r, 3).value or ""
            # generate alternating non-repeating characters
            new_txt = "".join(symbols[(i * 7 + r) % len(symbols)] for i in range(len(cur_txt)))
            ws.cell(r, 3, new_txt)
    f = os.path.join(TESTS_DIR, "broken_x_01_trap49_not_repeated.xlsx")
    modify_workbook(VALID_X, f, mod_x01)
    broken_manifest[f] = "V8"

    print(f"Successfully created {len(broken_manifest)} broken workbooks.")
    return broken_manifest


if __name__ == "__main__":
    generate_broken_cases()
