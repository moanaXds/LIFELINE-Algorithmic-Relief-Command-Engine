"""
load.py - Data loading and workbook parsing module for LIFELINE Phase 1 Validator.

Responsibilities:
1. Safely open the Excel workbook (.xlsx) using openpyxl in read-only mode.
2. Inspect the raw zip package for disallowed spreadsheet features:
   - Merged cells (<mergeCell / <mergeCells tags).
   - Spreadsheet formulas (formula cells or '=' prefixes).
3. Validate presence and strict ordering of all 20 required sheets.
4. Validate exact column header names for each worksheet.
5. Check cell formatting: plain ASCII text, strict integer types, no floats/booleans/None.
6. Check row sorting order: sorted primarily by case_id, secondarily by 2nd column.
7. Group worksheet rows by case_id for efficient per-case validation.

Viva Note:
This module enforces data integrity right at the boundary. By verifying row order,
types, ASCII encoding, and forbidden spreadsheet elements during the load pass,
subsequent validation stages (V1-V8) can rely on clean, typed data structures.
"""

import os
import string
import zipfile
import openpyxl

# Exactly 20 sheets in this specified order (Section 3 of project specification)
EXPECTED_SHEETS = [
    'cases',
    'crates',
    'locations',
    'roads',
    'waves',
    'radio_log',
    'radio_patterns',
    'radio_reports',
    'windows',
    'incidents',
    'sites',
    'tour',
    'pipeline_dims',
    'drum_prices',
    'sensor_edges',
    'sensor_cover',
    'safety_rules',
    'safety_planted',
    'rations',
    'claims'
]

# Exact expected headers for each sheet
EXPECTED_HEADERS = {
    'cases': [
        'case_id', 'group_seed', 'case_no', 'tier', 'scenario', 'capacity',
        'target_0', 'target_1', 'target_2', 'edit_bound', 'tour_length',
        'sensor_nodes', 'sensor_k', 'safety_vars', 'rations_target'
    ],
    'crates': ['case_id', 'crate_id', 'cat', 'weight', 'value', 'expiry', 'serial'],
    'locations': ['case_id', 'loc_id', 'type', 'penalty'],
    'roads': ['case_id', 'road_no', 'u', 'v', 'minutes', 'cable'],
    'waves': ['case_id', 'wave_no', 'road_no'],
    'radio_log': ['case_id', 'part', 'text'],
    'radio_patterns': ['case_id', 'pattern_no', 'pattern', 'count'],
    'radio_reports': ['case_id', 'report_a', 'report_b'],
    'windows': ['case_id', 'window_id', 'start', 'finish', 'value'],
    'incidents': ['case_id', 'alarm_id', 'tick', 'priority'],
    'sites': ['case_id', 'site_no', 'x', 'y'],
    'tour': ['case_id', 'step', 'site_no'],
    'pipeline_dims': ['case_id', 'idx', 'dim'],
    'drum_prices': ['case_id', 'length', 'price'],
    'sensor_edges': ['case_id', 'u', 'v'],
    'sensor_cover': ['case_id', 'node'],
    'safety_rules': ['case_id', 'rule_no', 'lit_1', 'lit_2', 'lit_3'],
    'safety_planted': ['case_id', 'switch', 'value'],
    'rations': ['case_id', 'item', 'value', 'planted'],
    'claims': ['case_id', 'cargo_opt', 'window_count_opt', 'window_value_opt', 'drum_opt', 'tour_opt', 'cover_min'],
}

# Set of columns expected to contain text (all other columns must be integers)
TEXT_COLUMNS = {
    'cases': {'case_id', 'tier'},
    'crates': {'case_id'},
    'locations': {'case_id', 'type'},
    'roads': {'case_id'},
    'waves': {'case_id'},
    'radio_log': {'case_id', 'text'},
    'radio_patterns': {'case_id', 'pattern'},
    'radio_reports': {'case_id', 'report_a', 'report_b'},
    'windows': {'case_id'},
    'incidents': {'case_id'},
    'sites': {'case_id'},
    'tour': {'case_id'},
    'pipeline_dims': {'case_id'},
    'drum_prices': {'case_id'},
    'sensor_edges': {'case_id'},
    'sensor_cover': {'case_id'},
    'safety_rules': {'case_id'},
    'safety_planted': {'case_id'},
    'rations': {'case_id'},
    'claims': {'case_id'}
}


def check_zip_features(filepath):
    """
    Examines the raw ZIP archive of the .xlsx file to detect:
    - Merged cells (<mergeCell or <mergeCells tags in worksheet XML).
    - Disallowed formula tags (<f> tags).
    Returns a list of error strings if any forbidden features are found.
    """
    errors = []
    if not zipfile.is_zipfile(filepath):
        return [f"File {filepath} is not a valid zip archive / xlsx spreadsheet."]

    with zipfile.ZipFile(filepath, 'r') as zf:
        for name in zf.namelist():
            if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
                xml_content = zf.read(name).decode('utf-8', errors='ignore')
                if '<mergeCells' in xml_content or '<mergeCell' in xml_content:
                    errors.append(f"V1: Merged cells detected in worksheet XML ({name}).")
                if '<f>' in xml_content or '<f ' in xml_content:
                    errors.append(f"V1: Formulas detected in worksheet XML ({name}).")
    return errors


def is_ascii(s):
    """Checks whether all characters in string s are plain ASCII."""
    try:
        s.encode('ascii')
        return True
    except (UnicodeEncodeError, AttributeError):
        return False


def load_dataset(filepath):
    """
    Loads cases.xlsx and organizes records by case_id.
    
    Returns:
        global_errors: list of errors at the workbook level (sheets, headers, zip-level checks).
        case_records: dict mapping case_id -> { sheet_name: list of row tuples/dicts }
        case_order: list of case_ids in the order defined in the 'cases' sheet.
        case_errors: dict mapping case_id -> list of structural/type errors found during load.
    """
    global_errors = []
    case_errors = {}
    case_records = {}
    case_order = []

    # 1. Inspect raw zip archive for merged cells and formula tags
    zip_errs = check_zip_features(filepath)
    if zip_errs:
        global_errors.extend(zip_errs)

    # 2. Open workbook with openpyxl in read-only mode
    try:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=False)
    except Exception as e:
        global_errors.append(f"V1: Failed to open workbook: {e}")
        return global_errors, case_records, case_order, case_errors

    # 3. Check sheet count, names, and exact order
    actual_sheets = wb.sheetnames
    if actual_sheets != EXPECTED_SHEETS:
        global_errors.append(
            f"V1: Sheet mismatch or incorrect ordering.\n"
            f"    Expected ({len(EXPECTED_SHEETS)}): {EXPECTED_SHEETS}\n"
            f"    Found ({len(actual_sheets)}): {actual_sheets}"
        )

    # 4. Read each sheet, check headers, types, ASCII, row order, and collect rows
    for sname in EXPECTED_SHEETS:
        if sname not in wb.sheetnames:
            continue  # Already flagged in sheet mismatch

        ws = wb[sname]
        expected_cols = EXPECTED_HEADERS.get(sname, [])
        text_cols = TEXT_COLUMNS.get(sname, set())

        headers = None
        row_idx = 0
        prev_case_id = None
        prev_col2 = None

        for row in ws.iter_rows():
            row_idx += 1
            row_values = [cell.value for cell in row]

            # Header row
            if row_idx == 1:
                headers = [str(v) if v is not None else '' for v in row_values]
                if headers != expected_cols:
                    global_errors.append(
                        f"V1: Sheet '{sname}' header mismatch.\n"
                        f"    Expected: {expected_cols}\n"
                        f"    Found:    {headers}"
                    )
                continue

            # Check for entirely empty rows
            if all(v is None for v in row_values):
                global_errors.append(f"V1: Empty row detected in sheet '{sname}' at row {row_idx}.")
                continue

            # Check row length matches header length
            if len(row_values) < len(expected_cols):
                global_errors.append(
                    f"V1: Sheet '{sname}' row {row_idx} has {len(row_values)} columns, expected {len(expected_cols)}."
                )
                continue

            # Trim trailing empty cells if any beyond expected length
            row_values = row_values[:len(expected_cols)]
            cid = str(row_values[0]) if row_values[0] is not None else ''

            if sname == 'cases' and cid not in case_order:
                case_order.append(cid)

            if cid not in case_records:
                case_records[cid] = {sheet: [] for sheet in EXPECTED_SHEETS}
            if cid not in case_errors:
                case_errors[cid] = []

            # Check sorting: sorted by case_id, then by 2nd column
            col2 = row_values[1] if len(row_values) > 1 else None
            if prev_case_id is not None:
                if cid < prev_case_id:
                    case_errors[cid].append(
                        f"V1: Row out of order in sheet '{sname}' at row {row_idx}: case_id '{cid}' after '{prev_case_id}'."
                    )
                elif cid == prev_case_id and col2 is not None and prev_col2 is not None:
                    # Secondary sort check: col2 must not decrease
                    if col2 < prev_col2:
                        case_errors[cid].append(
                            f"V1: Row out of order in sheet '{sname}' at row {row_idx}: "
                            f"2nd column value {col2} followed {prev_col2} for case '{cid}'."
                        )
            prev_case_id = cid
            prev_col2 = col2

            # Validate cell data types, ASCII encoding, formulas, and integer precision
            row_dict = {}
            for col_idx, (col_name, val) in enumerate(zip(expected_cols, row_values)):
                # Formula check
                if isinstance(val, str) and val.startswith('='):
                    case_errors[cid].append(
                        f"V1: Sheet '{sname}' row {row_idx} col '{col_name}' contains a formula: '{val}'."
                    )

                # None check
                if val is None:
                    case_errors[cid].append(
                        f"V1: Sheet '{sname}' row {row_idx} col '{col_name}' has missing / None value."
                    )
                    row_dict[col_name] = val
                    continue

                if col_name in text_cols:
                    # Must be text / string
                    if not isinstance(val, str):
                        case_errors[cid].append(
                            f"V1: Sheet '{sname}' row {row_idx} col '{col_name}' expected text string, got {type(val).__name__} ({val})."
                        )
                        row_dict[col_name] = str(val)
                    else:
                        if not is_ascii(val):
                            case_errors[cid].append(
                                f"V1: Sheet '{sname}' row {row_idx} col '{col_name}' contains non-ASCII characters."
                            )
                        row_dict[col_name] = val
                else:
                    # Must be strict integer (not bool, not float, not string)
                    if isinstance(val, bool) or not isinstance(val, int):
                        case_errors[cid].append(
                            f"V1: Sheet '{sname}' row {row_idx} col '{col_name}' expected integer, got {type(val).__name__} ({val})."
                        )
                        # Attempt safe cast for downstream validation
                        try:
                            row_dict[col_name] = int(val)
                        except Exception:
                            row_dict[col_name] = val
                    else:
                        row_dict[col_name] = val

            case_records[cid][sname].append(row_dict)

    wb.close()
    return global_errors, case_records, case_order, case_errors

