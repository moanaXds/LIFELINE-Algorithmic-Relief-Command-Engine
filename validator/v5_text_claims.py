"""
v5_text_claims.py - Radio log, pattern frequency, edit distance, and optimal claims validation.

Verifies:
1. Radio log:
   - Parts in consecutive order (1..num_parts).
   - Each part text length <= 10,000 symbols.
   - Text alphabet strictly within 38 symbols: A-Z, 0-9, '_', '-'.
2. Radio patterns:
   - Exactly 6 rows with pattern_no 0 to 5.
   - Pattern lengths strictly 2, 4, 8, 12, 20, 40 in that order.
   - Recounts occurrences in the joined log text with overlaps included.
   - Compares recomputed count with stored count:
     "V5: pattern {pno} stored {stored}, recomputed {recomputed}".
   - At least 2 patterns occur (count > 0) and at least 1 does not occur (count == 0).
3. Radio reports:
   - True Levenshtein edit distance computed via DP table.
   - Checks: true_dist <= edit_bound <= len(report_a) + len(report_b).
4. Exhaustive claims verification (Tier S only):
   - cargo_opt: 0/1 knapsack optimum within capacity.
   - window_count_opt: maximum compatible intervals (touching allowed: finish1 <= start2).
   - window_value_opt: maximum value of compatible intervals.
   - drum_opt: maximum revenue by integer cutting of drum of length L.
   - tour_opt: minimum closed Manhattan TSP tour visiting all sites starting at site 0.
   - cover_min: minimum vertex cover size touching every sensor edge.
"""

import string
from algos import (
    count_pattern_overlaps,
    levenshtein_distance,
    knapsack_01_exhaustive,
    interval_scheduling_exhaustive,
    rod_cutting_exhaustive,
    tsp_closed_manhattan_exhaustive,
    vertex_cover_min_exhaustive
)

ALLOWED_ALPHABET = set(string.ascii_uppercase + string.digits + '_-')
EXPECTED_PATTERN_LENGTHS = [2, 4, 8, 12, 20, 40]


def validate_case_v5(case_id, case_data):
    """
    Validates log text, pattern counts, edit distance bounds, and optimal claims for a single case.
    
    Args:
        case_id (str): Identifier, e.g., '18-00'.
        case_data (dict): Mapping of sheet_name -> list of row dicts.
        
    Returns:
        list of str: List of detected V5 errors.
    """
    errors = []

    cases_rows = case_data.get('cases', [])
    if not cases_rows:
        return errors
    case_meta = cases_rows[0]
    tier = case_meta.get('tier', 'S')
    capacity = case_meta.get('capacity', 0)
    stored_edit_bound = case_meta.get('edit_bound')
    sensor_nodes = case_meta.get('sensor_nodes', 0)

    radio_log = case_data.get('radio_log', [])
    radio_patterns = case_data.get('radio_patterns', [])
    radio_reports = case_data.get('radio_reports', [])
    crates = case_data.get('crates', [])
    windows = case_data.get('windows', [])
    drum_prices = case_data.get('drum_prices', [])
    sites = case_data.get('sites', [])
    sensor_edges = case_data.get('sensor_edges', [])
    claims_rows = case_data.get('claims', [])

    # -------------------------------------------------------------
    # 1. Radio Log Text Integrity
    # -------------------------------------------------------------
    full_log_text = ""
    for idx, part in enumerate(radio_log, start=1):
        p_no = part.get('part')
        txt = part.get('text', '')
        if p_no != idx:
            errors.append(f"V5: radio_log part {p_no} out of order, expected {idx}.")
        if len(txt) > 10000:
            errors.append(f"V5: radio_log part {p_no} length {len(txt)} exceeds 10,000 symbols limit.")
        if not set(txt).issubset(ALLOWED_ALPHABET):
            invalid = set(txt) - ALLOWED_ALPHABET
            errors.append(f"V5: radio_log part {p_no} contains invalid symbols outside 38-char alphabet: {invalid}.")
        full_log_text += txt

    # -------------------------------------------------------------
    # 2. Radio Patterns Recount & Constraints
    # -------------------------------------------------------------
    if len(radio_patterns) != 6:
        errors.append(f"V5: radio_patterns has {len(radio_patterns)} rows, expected exactly 6.")
    
    occurring_count = 0
    non_occurring_count = 0

    for idx, p in enumerate(radio_patterns):
        p_no = p.get('pattern_no')
        pat = p.get('pattern', '')
        stored_cnt = p.get('count')

        expected_len = EXPECTED_PATTERN_LENGTHS[idx] if idx < 6 else None
        if len(pat) != expected_len:
            errors.append(
                f"V5: pattern {p_no} length is {len(pat)}, expected {expected_len}."
            )

        if not set(pat).issubset(ALLOWED_ALPHABET):
            errors.append(f"V5: pattern {p_no} contains characters outside 38-symbol alphabet.")

        # Recount occurrences with overlaps
        recomputed_cnt = count_pattern_overlaps(full_log_text, pat)
        if stored_cnt != recomputed_cnt:
            errors.append(f"V5: pattern {p_no} stored {stored_cnt}, recomputed {recomputed_cnt}")

        if recomputed_cnt > 0:
            occurring_count += 1
        else:
            non_occurring_count += 1

    if occurring_count < 2:
        errors.append(f"V5: Only {occurring_count} patterns occur in the log (required: at least 2).")
    if non_occurring_count < 1:
        errors.append(f"V5: All patterns occur in the log (required: at least 1 must not occur).")

    # -------------------------------------------------------------
    # 3. Radio Reports Edit Distance Bound
    # -------------------------------------------------------------
    if radio_reports:
        rep_a = radio_reports[0].get('report_a', '')
        rep_b = radio_reports[0].get('report_b', '')
        true_dist = levenshtein_distance(rep_a, rep_b)
        max_bound = len(rep_a) + len(rep_b)

        if stored_edit_bound is None:
            errors.append("V5: edit_bound is missing in 'cases' sheet.")
        else:
            if not (true_dist <= stored_edit_bound <= max_bound):
                errors.append(
                    f"V5: edit_bound {stored_edit_bound} invalid (true edit distance is {true_dist}, max bound is {max_bound})."
                )

    # -------------------------------------------------------------
    # 4. Exhaustive Search Claims (Tier S Only)
    # -------------------------------------------------------------
    if tier == 'S':
        if not claims_rows:
            errors.append("V5: Missing claims row for Tier S case.")
            return errors

        claim = claims_rows[0]

        # 4a. cargo_opt
        crate_weights = [c['weight'] for c in crates]
        crate_values = [c['value'] for c in crates]
        recomputed_cargo = knapsack_01_exhaustive(crate_weights, crate_values, capacity)
        stored_cargo = claim.get('cargo_opt')
        if stored_cargo != recomputed_cargo:
            errors.append(f"V5: cargo_opt stored {stored_cargo}, recomputed {recomputed_cargo}.")

        # 4b. window_count_opt and window_value_opt
        intervals = [(w['start'], w['finish'], w['value']) for w in windows]
        recomputed_wcount, recomputed_wval = interval_scheduling_exhaustive(intervals)
        stored_wcount = claim.get('window_count_opt')
        stored_wval = claim.get('window_value_opt')
        if stored_wcount != recomputed_wcount:
            errors.append(f"V5: window_count_opt stored {stored_wcount}, recomputed {recomputed_wcount}.")
        if stored_wval != recomputed_wval:
            errors.append(f"V5: window_value_opt stored {stored_wval}, recomputed {recomputed_wval}.")

        # 4c. drum_opt
        prices_dict = {d['length']: d['price'] for d in drum_prices}
        drum_L = len(drum_prices)
        recomputed_drum = rod_cutting_exhaustive(drum_L, prices_dict)
        stored_drum = claim.get('drum_opt')
        if stored_drum != recomputed_drum:
            errors.append(f"V5: drum_opt stored {stored_drum}, recomputed {recomputed_drum}.")

        # 4d. tour_opt
        coords = [(s['x'], s['y']) for s in sorted(sites, key=lambda x: x['site_no'])]
        recomputed_tour = tsp_closed_manhattan_exhaustive(coords)
        stored_tour = claim.get('tour_opt')
        if stored_tour != recomputed_tour:
            errors.append(f"V5: tour_opt stored {stored_tour}, recomputed {recomputed_tour}.")

        # 4e. cover_min
        edge_tuples = [(e['u'], e['v']) for e in sensor_edges]
        recomputed_cover = vertex_cover_min_exhaustive(sensor_nodes, edge_tuples)
        stored_cover = claim.get('cover_min')
        if stored_cover != recomputed_cover:
            errors.append(f"V5: cover_min stored {stored_cover}, recomputed {recomputed_cover}.")

    return errors

