"""
v1_structure.py - Structure and schema validation for LIFELINE Phase 1 Validator.

Verifies:
1. Exactly 50 distinct case_ids (skipped under --partial).
2. Proper case_id format: '18-XX' where XX is two-digit case_no from 00 to 49.
3. Group seed matches required value (group_seed = 18).
4. Correct tier designation per case_no:
   - 00 to 19: Tier 'S'
   - 20 to 39: Tier 'M'
   - 40 to 45: Tier 'L'
   - 46 to 49: Tier 'X'
5. Correct disaster scenario index: scenario == (case_no % 6) + 1.
6. Exactly 1 row per case in the 'cases' sheet, and exactly 1 row in 'claims' for Tier S.
"""

def validate_case_v1(case_id, case_data):
    """
    Validates structural rules for a single case.
    
    Args:
        case_id (str): Identifier, e.g., '18-07'.
        case_data (dict): Mapping of sheet_name -> list of row dicts.
        
    Returns:
        list of str: Detected error messages for this case.
    """
    errors = []
    
    # Check 'cases' sheet presence and row count
    cases_rows = case_data.get('cases', [])
    if not cases_rows:
        errors.append(f"V1: Missing row in 'cases' sheet for case_id '{case_id}'.")
        return errors
    if len(cases_rows) > 1:
        errors.append(f"V1: Multiple rows ({len(cases_rows)}) in 'cases' sheet for case_id '{case_id}'.")
    
    row = cases_rows[0]
    
    # 1. Check group seed
    group_seed = row.get('group_seed')
    if group_seed != 18:
        errors.append(f"V1: group_seed is {group_seed}, expected 18.")
        
    # 2. Check case_no and case_id format
    case_no = row.get('case_no')
    if not isinstance(case_no, int) or not (0 <= case_no <= 49):
        errors.append(f"V1: case_no is {case_no}, expected integer in range 0..49.")
        return errors
    
    expected_case_id = f"18-{case_no:02d}"
    if case_id != expected_case_id:
        errors.append(f"V1: case_id '{case_id}' does not match expected '{expected_case_id}' for case_no {case_no}.")
        
    # 3. Check tier assignment
    tier = row.get('tier')
    if 0 <= case_no <= 19:
        expected_tier = 'S'
    elif 20 <= case_no <= 39:
        expected_tier = 'M'
    elif 40 <= case_no <= 45:
        expected_tier = 'L'
    else:
        expected_tier = 'X'
        
    if tier != expected_tier:
        errors.append(f"V1: tier is '{tier}', expected '{expected_tier}' for case_no {case_no}.")
        
    # 4. Check scenario assignment: scenario = (case_no % 6) + 1
    scenario = row.get('scenario')
    expected_scenario = (case_no % 6) + 1
    if scenario != expected_scenario:
        errors.append(f"V1: scenario is {scenario}, expected {expected_scenario} for case_no {case_no}.")

    # 5. Check claims sheet row requirement: Tier S has 1 row; other tiers have 0 rows
    claims_rows = case_data.get('claims', [])
    if tier == 'S':
        if len(claims_rows) != 1:
            errors.append(f"V1: Tier S case must have exactly 1 row in 'claims', found {len(claims_rows)}.")
    else:
        if len(claims_rows) > 0:
            errors.append(f"V1: Tier {tier} case should have no rows in 'claims', found {len(claims_rows)}.")
            
    # 6. Verify non-empty data in required sheets
    sheets_requiring_rows = [
        'crates', 'locations', 'roads', 'waves', 'radio_log',
        'radio_patterns', 'radio_reports', 'windows', 'incidents',
        'sites', 'tour', 'pipeline_dims', 'drum_prices', 'sensor_edges',
        'sensor_cover', 'safety_rules', 'safety_planted', 'rations'
    ]
    for sname in sheets_requiring_rows:
        if not case_data.get(sname):
            errors.append(f"V1: Sheet '{sname}' has 0 rows for case_id '{case_id}'.")

    return errors


def validate_global_v1(all_case_ids, partial=False):
    """
    Validates global structure rules across all cases.
    
    Args:
        all_case_ids (list of str): List of loaded case IDs.
        partial (bool): If True, skips 50-case count check.
        
    Returns:
        list of str: Global structural errors.
    """
    errors = []
    if partial:
        return errors
        
    # Full dataset check: exactly 50 distinct case IDs from 18-00 to 18-49
    expected_ids = [f"18-{i:02d}" for i in range(50)]
    if len(all_case_ids) != 50:
        errors.append(f"V1 GLOBAL: Expected exactly 50 cases, found {len(all_case_ids)}.")
        
    missing = set(expected_ids) - set(all_case_ids)
    if missing:
        errors.append(f"V1 GLOBAL: Missing required case_ids: {sorted(list(missing))}.")
        
    extra = set(all_case_ids) - set(expected_ids)
    if extra:
        errors.append(f"V1 GLOBAL: Unexpected extra case_ids: {sorted(list(extra))}.")
        
    return errors

