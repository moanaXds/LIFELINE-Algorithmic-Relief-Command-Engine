"""
v7_signatures.py - Disaster scenario signature rules and global variety validation.

Verifies:
1. Scenario signature rules (cases 0..45, where study = (case_no % 6) + 1):
   - 1 Delta Flood: avg degree in [2.2, 3.2]; >= 40% locations penalty >= 2; >= 3 waves; cat 0+1 crates >= 55%.
   - 2 Mountain Earthquake: avg degree in [2.0, 2.6]; cat 2+3 crates >= 45%; mean alarm priority >= 6.0.
   - 3 Coastal Cyclone: >= 25% locations shelters; >= 3 waves; avg window strict overlaps >= 2.0; log uses >= 30 of 38 symbols.
   - 4 Urban Flash Flood: avg degree >= 3.5; on Tiers M/L alarms per tick >= 1.5; cat 4 crates >= 10%.
   - 5 Landslide Corridor: avg degree <= 2.4; max degree <= 4; farthest location from HQ >= floor(V/4) hops;
     >= 3 waves; union of all closed roads leaves at least one target unreachable from HQ.
   - 6 Outbreak Camp: cat 2+1 crates >= 55%; >= 50% crates expire <= 300; one symbol >= 25% of log.
2. Tiers M/L general rules:
   - alarms per tick in [1.2, 1.8] (count / (last_tick + 1)).
   - >= 6 distinct priorities including priority 1.
   - with >= 8 windows, at least 2 touching pairs (finish == other start).
3. Global variety rules across all 50 cases (skipped under --partial):
   - Variety 1: In >= 5 Tier S cases, greedy knapsack is not optimal.
   - Variety 2: In >= 5 Tier S cases, for some target, every fewest-roads route costs more than a cheapest route.
   - Variety 3: Across 26 M+L cases, safety rules/vars in [2.5, 6.0]; >= 5 below 3.5, >= 8 in [3.5, 4.8], >= 5 above 4.8.
   - Variety 4: No two cases equal in any module of size >= 8.
"""

from collections import Counter, defaultdict, deque
import hashlib
import math
from algos import (
    greedy_knapsack_value,
    dijkstra_cheapest_paths,
    min_cost_among_fewest_roads,
    bfs_hops_from_source
)


def validate_case_v7(case_id, case_data):
    """
    Validates scenario signature rules for a single case (cases 0..45).
    Hostile trap cases (46..49) have signature rules waived.
    
    Args:
        case_id (str): Identifier, e.g., '18-00'.
        case_data (dict): Mapping of sheet_name -> list of row dicts.
        
    Returns:
        list of str: Detected V7 errors for this case.
    """
    errors = []

    cases_rows = case_data.get('cases', [])
    if not cases_rows:
        return errors
    case_meta = cases_rows[0]
    case_no = case_meta.get('case_no', 0)
    tier = case_meta.get('tier', 'S')
    scenario = case_meta.get('scenario', 1)
    targets = [case_meta.get('target_0'), case_meta.get('target_1'), case_meta.get('target_2')]

    # Trap cases (46-49) have signature rules waived per PDF Section 2
    if case_no >= 46:
        return errors

    crates = case_data.get('crates', [])
    locations = case_data.get('locations', [])
    roads = case_data.get('roads', [])
    waves = case_data.get('waves', [])
    windows = case_data.get('windows', [])
    incidents = case_data.get('incidents', [])
    radio_log = case_data.get('radio_log', [])

    V = len(locations)
    E = len(roads)
    avg_degree = (2.0 * E) / V if V > 0 else 0.0
    distinct_waves = set(w.get('wave_no') for w in waves if w.get('wave_no') is not None)
    num_waves = len(distinct_waves)
    num_crates = len(crates)

    # -------------------------------------------------------------
    # 1. Disaster Scenario Signatures
    # -------------------------------------------------------------
    if scenario == 1:
        # Delta Flood: avg deg 2.2-3.2; >= 40% locations penalty >= 2; >= 3 waves; cat 0+1 crates >= 55%
        if not (2.2 <= avg_degree <= 3.2):
            errors.append(f"V7: Scenario 1 (Delta Flood) average degree {avg_degree:.2f} not in [2.2, 3.2].")

        pen_ge2 = sum(1 for loc in locations if loc.get('penalty', 0) >= 2)
        pen_pct = (pen_ge2 / V) if V > 0 else 0
        if pen_pct < 0.40:
            errors.append(
                f"V7: Scenario 1 (Delta Flood) {pen_pct*100:.1f}% locations have penalty >= 2 (required: >= 40%)."
            )

        if num_waves < 3:
            errors.append(f"V7: Scenario 1 (Delta Flood) has {num_waves} waves (required: >= 3).")

        cat_01 = sum(1 for c in crates if c.get('cat') in (0, 1))
        cat_01_pct = (cat_01 / num_crates) if num_crates > 0 else 0
        if cat_01_pct < 0.55:
            errors.append(
                f"V7: Scenario 1 (Delta Flood) food/water crates {cat_01_pct*100:.1f}% (required: >= 55%)."
            )

    elif scenario == 2:
        # Mountain Earthquake: avg deg 2.0-2.6; cat 2+3 crates >= 45%; mean alarm priority >= 6.0
        if not (2.0 <= avg_degree <= 2.6):
            errors.append(f"V7: Scenario 2 (Mountain Earthquake) average degree {avg_degree:.2f} not in [2.0, 2.6].")

        cat_23 = sum(1 for c in crates if c.get('cat') in (2, 3))
        cat_23_pct = (cat_23 / num_crates) if num_crates > 0 else 0
        if cat_23_pct < 0.45:
            errors.append(
                f"V7: Scenario 2 (Mountain Earthquake) medicine/tool crates {cat_23_pct*100:.1f}% (required: >= 45%)."
            )

        if incidents:
            mean_prio = sum(inc.get('priority', 0) for inc in incidents) / len(incidents)
            if mean_prio < 6.0:
                errors.append(
                    f"V7: Scenario 2 (Mountain Earthquake) mean alarm priority {mean_prio:.2f} < 6.0."
                )

    elif scenario == 3:
        # Coastal Cyclone: >= 25% locations are shelters; >= 3 waves; each window overlaps >= 2 other windows on avg; log uses >= 30 of 38 symbols
        shelters = sum(1 for loc in locations if loc.get('type') == 'S')
        shelter_pct = (shelters / V) if V > 0 else 0
        if shelter_pct < 0.25:
            errors.append(
                f"V7: Scenario 3 (Coastal Cyclone) shelter locations {shelter_pct*100:.1f}% (required: >= 25%)."
            )

        if num_waves < 3:
            errors.append(f"V7: Scenario 3 (Coastal Cyclone) has {num_waves} waves (required: >= 3).")

        # Window strict overlaps average
        if windows:
            # Sort windows by start time for efficient overlap counting
            w_intervals = [(w.get('start', 0), w.get('finish', 0)) for w in windows]
            total_overlaps = 0
            for i, (s1, f1) in enumerate(w_intervals):
                overlaps_i = 0
                for j, (s2, f2) in enumerate(w_intervals):
                    if i != j:
                        # Strict overlap: touching excluded (max(s1, s2) < min(f1, f2))
                        if max(s1, s2) < min(f1, f2):
                            overlaps_i += 1
                total_overlaps += overlaps_i
            avg_overlaps = total_overlaps / len(windows)
            if avg_overlaps < 2.0:
                errors.append(
                    f"V7: Scenario 3 (Coastal Cyclone) avg window overlaps {avg_overlaps:.2f} < 2.0."
                )

        full_log = "".join(p.get('text', '') for p in radio_log)
        distinct_syms = len(set(full_log))
        if distinct_syms < 30:
            errors.append(
                f"V7: Scenario 3 (Coastal Cyclone) radio log uses {distinct_syms} symbols (required: >= 30)."
            )

    elif scenario == 4:
        # Urban Flash Flood: avg deg >= 3.5; tiers M/L alarms per tick >= 1.5; cat 4 crates >= 10%
        if avg_degree < 3.5:
            errors.append(f"V7: Scenario 4 (Urban Flash Flood) average degree {avg_degree:.2f} < 3.5.")

        cat_4 = sum(1 for c in crates if c.get('cat') == 4)
        cat_4_pct = (cat_4 / num_crates) if num_crates > 0 else 0
        if cat_4_pct < 0.10:
            errors.append(
                f"V7: Scenario 4 (Urban Flash Flood) rare crates {cat_4_pct*100:.1f}% < 10%."
            )

        if tier in ('M', 'L') and incidents:
            last_tick = incidents[-1].get('tick', 0)
            alarms_per_tick = len(incidents) / (last_tick + 1)
            if alarms_per_tick < 1.5:
                errors.append(
                    f"V7: Scenario 4 (Urban Flash Flood) alarms per tick {alarms_per_tick:.2f} < 1.5."
                )

    elif scenario == 5:
        # Landslide Corridor: deg <= 2.4; max degree <= 4; farthest location from HQ >= floor(V/4) hops;
        # >= 3 waves; after removing all closed roads, at least one target unreachable from 0
        if avg_degree > 2.4:
            errors.append(f"V7: Scenario 5 (Landslide Corridor) average degree {avg_degree:.2f} > 2.4.")

        adj_degrees = defaultdict(int)
        for r in roads:
            adj_degrees[r['u']] += 1
            adj_degrees[r['v']] += 1
        max_deg = max(adj_degrees.values()) if adj_degrees else 0
        if max_deg > 4:
            errors.append(f"V7: Scenario 5 (Landslide Corridor) max node degree {max_deg} > 4.")

        if num_waves < 3:
            errors.append(f"V7: Scenario 5 (Landslide Corridor) has {num_waves} waves (required: >= 3).")

        # Farthest location from HQ (node 0) hops >= floor(V/4)
        edge_pairs = [(r['u'], r['v']) for r in roads]
        hops_dict = bfs_hops_from_source(V, edge_pairs, source=0)
        max_hops = max(hops_dict.values()) if hops_dict else 0
        req_hops = math.floor(V / 4)
        if max_hops < req_hops:
            errors.append(
                f"V7: Scenario 5 (Landslide Corridor) farthest location is {max_hops} hops from HQ, expected >= {req_hops}."
            )

        # Closure cut: after removing ALL closed roads, at least one target is unreachable from HQ
        closed_road_nos = set(w.get('road_no') for w in waves)
        open_edges = [(r['u'], r['v']) for r in roads if r.get('road_no') not in closed_road_nos]
        open_hops = bfs_hops_from_source(V, open_edges, source=0)

        reachable_targets = [t for t in targets if t in open_hops]
        if len(reachable_targets) == len(targets):
            errors.append(
                "V7: Scenario 5 (Landslide Corridor) all targets remain reachable after removing all closed roads."
            )

    elif scenario == 6:
        # Outbreak Camp: cat 2+1 crates >= 55%; >= half of crates have expiry <= 300; one symbol >= 25% of log
        cat_12 = sum(1 for c in crates if c.get('cat') in (1, 2))
        cat_12_pct = (cat_12 / num_crates) if num_crates > 0 else 0
        if cat_12_pct < 0.55:
            errors.append(
                f"V7: Scenario 6 (Outbreak Camp) medicine/water crates {cat_12_pct*100:.1f}% < 55%."
            )

        exp_300 = sum(1 for c in crates if c.get('expiry', 0) <= 300)
        exp_300_pct = (exp_300 / num_crates) if num_crates > 0 else 0
        if exp_300_pct < 0.50:
            errors.append(
                f"V7: Scenario 6 (Outbreak Camp) crates expiring <= 300 hrs {exp_300_pct*100:.1f}% < 50%."
            )

        full_log = "".join(p.get('text', '') for p in radio_log)
        if full_log:
            counts = Counter(full_log)
            top_sym, top_cnt = counts.most_common(1)[0]
            top_pct = top_cnt / len(full_log)
            if top_pct < 0.25:
                errors.append(
                    f"V7: Scenario 6 (Outbreak Camp) most frequent symbol '{top_sym}' is {top_pct*100:.1f}% < 25%."
                )

    # -------------------------------------------------------------
    # 2. General Tiers M and L Rules
    # -------------------------------------------------------------
    if tier in ('M', 'L'):
        # Alarms per tick between 1.2 and 1.8 (count / (last tick + 1))
        if incidents:
            last_tick = incidents[-1].get('tick', 0)
            apt = len(incidents) / (last_tick + 1)
            if not (1.2 <= apt <= 1.8):
                errors.append(f"V7: Tier {tier} alarms per tick {apt:.2f} not in [1.2, 1.8].")

            priorities = set(inc.get('priority') for inc in incidents)
            if len(priorities) < 6:
                errors.append(f"V7: Tier {tier} has {len(priorities)} distinct priorities (required: >= 6).")
            if 1 not in priorities:
                errors.append(f"V7: Tier {tier} priorities missing required priority 1.")

        # With >= 8 windows, at least 2 touching pairs (finish == other start)
        if len(windows) >= 8:
            start_counts = Counter(w.get('start') for w in windows)
            touching_pairs = sum(start_counts.get(w.get('finish'), 0) for w in windows)
            if touching_pairs < 2:
                errors.append(
                    f"V7: Tier {tier} has {touching_pairs} touching window pairs (required: >= 2)."
                )

    return errors


def validate_global_variety(all_cases_data, partial=False):
    """
    Validates the 4 global variety rules across the dataset.
    Skipped when partial=True.
    """
    errors = []
    if partial:
        return errors

    # Filter Tier S cases (18-00 to 18-19)
    tier_s_cases = []
    # Filter Tiers M and L cases (18-20 to 18-45)
    tier_ml_cases = []

    for cid, cdata in all_cases_data.items():
        c_rows = cdata.get('cases', [])
        if not c_rows:
            continue
        tier = c_rows[0].get('tier')
        if tier == 'S':
            tier_s_cases.append((cid, cdata))
        elif tier in ('M', 'L'):
            tier_ml_cases.append((cid, cdata))

    # -------------------------------------------------------------
    # Variety Rule 1: In >= 5 Tier S cases, greedy knapsack is not optimal
    # -------------------------------------------------------------
    subopt_greedy_count = 0
    for cid, cdata in tier_s_cases:
        cap = cdata['cases'][0].get('capacity', 0)
        crates = cdata.get('crates', [])
        claims = cdata.get('claims', [])
        if claims:
            optimal_val = claims[0].get('cargo_opt', 0)
            greedy_val = greedy_knapsack_value(crates, cap)
            if greedy_val < optimal_val:
                subopt_greedy_count += 1

    if subopt_greedy_count < 5:
        errors.append(
            f"V7 GLOBAL (Variety 1): Greedy knapsack is suboptimal in only {subopt_greedy_count} "
            f"Tier S cases (required: >= 5)."
        )

    # -------------------------------------------------------------
    # Variety Rule 2: In >= 5 Tier S cases, for some target, every fewest-roads
    # route costs more than a cheapest route
    # -------------------------------------------------------------
    route_divergence_count = 0
    for cid, cdata in tier_s_cases:
        cmeta = cdata['cases'][0]
        targets = [cmeta.get('target_0'), cmeta.get('target_1'), cmeta.get('target_2')]
        locations = cdata.get('locations', [])
        roads = cdata.get('roads', [])
        penalties = {l.get('loc_id'): l.get('penalty', 0) for l in locations}
        V = len(locations)

        cheapest_dists = dijkstra_cheapest_paths(V, roads, penalties, source=0)
        diverged = False
        for t in targets:
            cheapest_cost = cheapest_dists.get(t, float('inf'))
            min_fewest_cost = min_cost_among_fewest_roads(V, roads, penalties, source=0, target=t)
            if min_fewest_cost > cheapest_cost:
                diverged = True
                break

        if diverged:
            route_divergence_count += 1

    if route_divergence_count < 5:
        errors.append(
            f"V7 GLOBAL (Variety 2): Fewest-roads vs cheapest route divergence in only "
            f"{route_divergence_count} Tier S cases (required: >= 5)."
        )

    # -------------------------------------------------------------
    # Variety Rule 3: Tiers M+L (26 cases): safety rules per switch in [2.5, 6.0];
    # >= 5 cases below 3.5, >= 8 in [3.5, 4.8], >= 5 above 4.8
    # -------------------------------------------------------------
    if len(tier_ml_cases) != 26:
        errors.append(
            f"V7 GLOBAL (Variety 3): Expected 26 cases in Tiers M and L, found {len(tier_ml_cases)}."
        )

    below_35 = 0
    in_35_48 = 0
    above_48 = 0

    for cid, cdata in tier_ml_cases:
        sv = cdata['cases'][0].get('safety_vars', 0)
        nr = len(cdata.get('safety_rules', []))
        if sv > 0:
            ratio = nr / sv
            if ratio < 2.5 or ratio > 6.0:
                errors.append(
                    f"V7 GLOBAL (Variety 3): Case {cid} safety ratio {ratio:.2f} not in [2.5, 6.0]."
                )
            if ratio < 3.5:
                below_35 += 1
            elif ratio <= 4.8:
                in_35_48 += 1
            else:
                above_48 += 1

    if below_35 < 5:
        errors.append(f"V7 GLOBAL (Variety 3): {below_35} M+L cases with safety ratio < 3.5 (required: >= 5).")
    if in_35_48 < 8:
        errors.append(f"V7 GLOBAL (Variety 3): {in_35_48} M+L cases with safety ratio in [3.5, 4.8] (required: >= 8).")
    if above_48 < 5:
        errors.append(f"V7 GLOBAL (Variety 3): {above_48} M+L cases with safety ratio > 4.8 (required: >= 5).")

    # -------------------------------------------------------------
    # Variety Rule 4: No two cases equal in any module of size >= 8
    # (sheet rows without case_id, log, reports)
    # -------------------------------------------------------------
    sheets_to_check = [
        'crates', 'locations', 'roads', 'waves', 'radio_patterns',
        'windows', 'incidents', 'sites', 'tour', 'pipeline_dims',
        'drum_prices', 'sensor_edges', 'sensor_cover', 'safety_rules',
        'safety_planted', 'rations'
    ]

    collisions = []
    for mod_name in sheets_to_check:
        seen_module_hashes = {}
        for cid, cdata in all_cases_data.items():
            rows = cdata.get(mod_name, [])
            if len(rows) >= 8:
                # Strip case_id from rows for content comparison
                content_tuples = []
                for r in rows:
                    content_tuples.append(tuple(v for k, v in sorted(r.items()) if k != 'case_id'))
                h = hashlib.sha256(str(content_tuples).encode('utf-8')).hexdigest()
                if h in seen_module_hashes:
                    collisions.append((seen_module_hashes[h], cid, mod_name))
                else:
                    seen_module_hashes[h] = cid

    # Radio log check
    seen_log_hashes = {}
    for cid, cdata in all_cases_data.items():
        joined_log = "".join(p.get('text', '') for p in cdata.get('radio_log', []))
        if len(joined_log) >= 8:
            h = hashlib.sha256(joined_log.encode('utf-8')).hexdigest()
            if h in seen_log_hashes:
                collisions.append((seen_log_hashes[h], cid, 'radio_log'))
            else:
                seen_log_hashes[h] = cid

    # Radio reports check
    seen_rep_hashes = {}
    for cid, cdata in all_cases_data.items():
        reps = cdata.get('radio_reports', [])
        if reps:
            rep_a = reps[0].get('report_a', '')
            rep_b = reps[0].get('report_b', '')
            if len(rep_a) + len(rep_b) >= 8:
                h = hashlib.sha256((rep_a + "||" + rep_b).encode('utf-8')).hexdigest()
                if h in seen_rep_hashes:
                    collisions.append((seen_rep_hashes[h], cid, 'radio_reports'))
                else:
                    seen_rep_hashes[h] = cid

    if collisions:
        for c1, c2, mod in collisions:
            errors.append(
                f"V7 GLOBAL (Variety 4): Duplicate module '{mod}' of size >= 8 detected between cases {c1} and {c2}."
            )

    return errors

