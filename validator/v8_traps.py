"""
v8_traps.py - Hostile trap cases validation (Cases 46-49) for LIFELINE Phase 1 Validator.

Per PDF Section 2, cases 46 to 49 are deliberately hostile but complete, valid cases (Tier X).
Their case study signature rules (V7) are waived, but V1-V6 and the specific trap requirements apply:

1. Case 46 (Dock-order trap):
   - 1,500 to 3,000 crates.
   - The crate list, in crate_id order, is already monotone (all non-decreasing or all non-increasing)
     in at least 3 of the 5 fields: value, weight, expiry, serial, and value-per-kg (exact cross-multiplication).

2. Case 47 (Best-looking-crate trap):
   - 12 to 60 crates.
   - Taking crates in decreasing order of value per kg (skipping non-fitting crates) achieves at most
     60% of the true optimal total value (recomputed via 0/1 knapsack DP).

3. Case 48 (Shortest-looks-cheapest trap):
   - 1,500 to 3,000 locations.
   - Graph diameter (longest distance between two locations) is at least 500 roads (hops).
     Lower bound verified via double-sweep BFS (with full BFS fallback).
   - For at least one target, every route with the fewest roads costs at least 1.5 times a cheapest route
     (2 * minCostAmongFewestRoads >= 3 * cheapestCost).

4. Case 49 (Near-miss trap):
   - 50,000 to 100,000 log symbols.
   - At least 90% of the log is a repetition of one block of at most 8 symbols
     (for b=1..8, per residue class mod b take the most common symbol, sum matches / length >= 0.90).
   - For at least 4 patterns, the first (length - 1) symbols match the log at >= half of all start
     positions (denominator: N - len + 1).
"""

from collections import Counter
from algos import (
    greedy_knapsack_value,
    knapsack_01_dp,
    double_sweep_bfs,
    dijkstra_cheapest_paths,
    min_cost_among_fewest_roads
)


def is_sequence_monotone(seq):
    """
    Checks if a numeric sequence is all non-decreasing or all non-increasing.
    """
    if len(seq) <= 1:
        return True
    is_non_dec = all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1))
    if is_non_dec:
        return True
    is_non_inc = all(seq[i] >= seq[i + 1] for i in range(len(seq) - 1))
    return is_non_inc


def is_vpk_monotone(crates):
    """
    Checks if value-per-kg is monotone using exact cross-multiplication:
    v1 / w1 <= v2 / w2 <=> v1 * w2 <= v2 * w1
    """
    if len(crates) <= 1:
        return True
    # Non-decreasing check
    non_dec = all(
        crates[i]['value'] * crates[i + 1]['weight'] <= crates[i + 1]['value'] * crates[i]['weight']
        for i in range(len(crates) - 1)
    )
    if non_dec:
        return True
    # Non-increasing check
    non_inc = all(
        crates[i]['value'] * crates[i + 1]['weight'] >= crates[i + 1]['value'] * crates[i]['weight']
        for i in range(len(crates) - 1)
    )
    return non_inc


def validate_case_v8(case_id, case_data):
    """
    Validates hostile trap requirements for cases 46-49.
    
    Args:
        case_id (str): Identifier, e.g., '18-46'.
        case_data (dict): Mapping of sheet_name -> list of row dicts.
        
    Returns:
        list of str: Detected V8 errors for this case.
    """
    errors = []

    cases_rows = case_data.get('cases', [])
    if not cases_rows:
        return errors
    case_meta = cases_rows[0]
    case_no = case_meta.get('case_no', 0)

    # Only applies to hostile trap cases 46..49
    if case_no < 46 or case_no > 49:
        return errors

    crates = case_data.get('crates', [])
    locations = case_data.get('locations', [])
    roads = case_data.get('roads', [])
    radio_log = case_data.get('radio_log', [])
    radio_patterns = case_data.get('radio_patterns', [])

    # -------------------------------------------------------------
    # Case 46: Dock-Order Trap
    # -------------------------------------------------------------
    if case_no == 46:
        # Sort crates in crate_id order
        sorted_crates = sorted(crates, key=lambda c: c.get('crate_id', 0))
        n_crates = len(sorted_crates)
        if not (1500 <= n_crates <= 3000):
            errors.append(f"V8: Case 46 crate count {n_crates} not in range [1500, 3000].")

        m_val = is_sequence_monotone([c.get('value', 0) for c in sorted_crates])
        m_wt = is_sequence_monotone([c.get('weight', 0) for c in sorted_crates])
        m_exp = is_sequence_monotone([c.get('expiry', 0) for c in sorted_crates])
        m_ser = is_sequence_monotone([c.get('serial', 0) for c in sorted_crates])
        m_vpk = is_vpk_monotone(sorted_crates)

        monotone_count = sum([m_val, m_wt, m_exp, m_ser, m_vpk])
        if monotone_count < 3:
            errors.append(
                f"V8: Case 46 (Dock-Order Trap) is monotone in only {monotone_count} of 5 fields "
                f"(value={m_val}, weight={m_wt}, expiry={m_exp}, serial={m_ser}, vpk={m_vpk}; required: >= 3)."
            )

    # -------------------------------------------------------------
    # Case 47: Best-Looking-Crate Trap
    # -------------------------------------------------------------
    elif case_no == 47:
        n_crates = len(crates)
        if not (12 <= n_crates <= 60):
            errors.append(f"V8: Case 47 crate count {n_crates} not in range [12, 60].")

        capacity = case_meta.get('capacity', 0)
        greedy_val = greedy_knapsack_value(crates, capacity)
        weights = [c.get('weight', 0) for c in crates]
        values = [c.get('value', 0) for c in crates]
        opt_val = knapsack_01_dp(weights, values, capacity)

        if opt_val > 0:
            ratio = greedy_val / opt_val
            # Must achieve at most 60% of true optimum
            if ratio > 0.60:
                errors.append(
                    f"V8: Case 47 (Best-Looking-Crate Trap) greedy knapsack reaches {ratio*100:.2f}% "
                    f"({greedy_val}/{opt_val}) of optimum (required: <= 60%)."
                )

    # -------------------------------------------------------------
    # Case 48: Shortest-Looks-Cheapest Trap
    # -------------------------------------------------------------
    elif case_no == 48:
        V = len(locations)
        if not (1500 <= V <= 3000):
            errors.append(f"V8: Case 48 locations count {V} not in range [1500, 3000].")

        # 1. Longest distance of at least 500 roads between two locations
        edges = [(r['u'], r['v']) for r in roads]
        diam_lower_bound = double_sweep_bfs(V, edges)
        if diam_lower_bound < 500:
            errors.append(
                f"V8: Case 48 graph diameter lower bound {diam_lower_bound} is less than 500 roads."
            )

        # 2. For at least 1 target, 2 * minCostAmongFewestRoads >= 3 * cheapestCost
        targets = [case_meta.get('target_0'), case_meta.get('target_1'), case_meta.get('target_2')]
        penalties = {l.get('loc_id'): l.get('penalty', 0) for l in locations}
        cheapest_dists = dijkstra_cheapest_paths(V, roads, penalties, source=0)

        route_ratio_satisfied = False
        for t in targets:
            cheap_cost = cheapest_dists.get(t, float('inf'))
            min_fewest_cost = min_cost_among_fewest_roads(V, roads, penalties, source=0, target=t)
            if 2 * min_fewest_cost >= 3 * cheap_cost:
                route_ratio_satisfied = True
                break

        if not route_ratio_satisfied:
            errors.append(
                "V8: Case 48 fails condition: every route with fewest roads must cost >= 1.5x a cheapest route for >= 1 target."
            )

    # -------------------------------------------------------------
    # Case 49: Near-Miss Trap
    # -------------------------------------------------------------
    elif case_no == 49:
        full_log = "".join(p.get('text', '') for p in radio_log)
        N = len(full_log)
        if not (50000 <= N <= 100000):
            errors.append(f"V8: Case 49 log length {N} not in range [50000, 100000].")

        # 1. At least 90% of log is one repeated block of <= 8 symbols
        # For b = 1..8, per residue class mod b, take the most common symbol
        found_block = False
        max_block_pct = 0.0
        for b in range(1, 9):
            matches = 0
            for r in range(b):
                chars_in_residue = full_log[r::b]
                if chars_in_residue:
                    c = Counter(chars_in_residue)
                    matches += c.most_common(1)[0][1]
            pct = matches / N if N > 0 else 0
            if pct > max_block_pct:
                max_block_pct = pct
            if pct >= 0.90:
                found_block = True
                break

        if not found_block:
            errors.append(
                f"V8: Case 49 log repetition percentage {max_block_pct*100:.2f}% < 90% for blocks of length <= 8."
            )

        # 2. For at least 4 patterns, first (len - 1) symbols match log at >= half of all start positions
        # Denominator: N - len + 1
        near_miss_matches = 0
        for p in radio_patterns:
            pat = p.get('pattern', '')
            L = len(pat)
            if L <= 1:
                continue
            prefix = pat[:L - 1]
            denom = N - L + 1
            if denom <= 0:
                continue

            # Count start positions i in 0..denom-1 where full_log[i:i+L-1] == prefix
            count_matches = 0
            for i in range(denom):
                if full_log[i:i + L - 1] == prefix:
                    count_matches += 1

            if 2 * count_matches >= denom:
                near_miss_matches += 1

        if near_miss_matches < 4:
            errors.append(
                f"V8: Case 49 has only {near_miss_matches} patterns whose (len-1) prefix matches >= 50% "
                f"of start positions (required: >= 4)."
            )

    return errors

