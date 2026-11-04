"""
case_builder.py - Deterministic Generator for all 20 Sheets of LIFELINE Cases
Builds cases 00-49 with full compliance to tier ranges, scenario signature rules,
trap requirements, planted answers, variety conditions, and tier-S claims.
"""

import math
import random
from collections import deque
from generator.solvers import (
    solve_knapsack,
    solve_greedy_knapsack,
    solve_interval_scheduling_count,
    solve_interval_scheduling_weight,
    solve_rod_cutting,
    solve_tsp_manhattan,
    nearest_neighbor_tour_length,
    solve_min_vertex_cover,
    levenshtein_distance,
    count_overlapping_occurrences,
    dijkstra_cheapest_cost,
    shortest_hop_cost
)

ALPHABET_38 = [chr(c) for c in range(ord('A'), ord('Z') + 1)] + \
              [chr(c) for c in range(ord('0'), ord('9') + 1)] + ['_', '-']

def generate_case(seed, case_no):
    """
    Generate all data for case_no (0 to 49) deterministically given group seed.
    Returns a dictionary of records for each sheet for this case.
    """
    case_id = f"{seed}-{case_no:02d}"
    
    # Tier assignment
    if 0 <= case_no <= 19:
        tier = 'S'
    elif 20 <= case_no <= 39:
        tier = 'M'
    elif 40 <= case_no <= 45:
        tier = 'L'
    else:
        tier = 'X'
        
    scenario = (case_no % 6) + 1
    
    # Initialize deterministic RNG for this case
    rng = random.Random(seed * 10007 + case_no * 101)
    
    # -------------------------------------------------------------
    # 1. CRATES & CAPACITY
    # -------------------------------------------------------------
    if tier == 'S':
        if case_no < 5:
            n_crates = rng.randint(8, 12)
        else:
            n_crates = rng.randint(8, 20)
    elif tier == 'M':
        n_crates = rng.randint(40, 200)
    elif tier == 'L':
        n_crates = rng.randint(500, 1500)
    else: # tier X
        if case_no == 46: # Dock-order trap
            n_crates = rng.randint(1500, 3000)
        elif case_no == 47: # Best-looking-crate trap
            n_crates = 16 # in [12, 60]
        else:
            n_crates = rng.randint(500, 1500)
            
    crates = []
    
    if case_no == 46:
        # Trap 46: Dock-order trap
        # List in crate_id order is monotone in at least 3 of 5 fields:
        # value, weight, expiry, serial, value-per-kg.
        # Make weight, value, and serial all non-decreasing!
        weights = sorted([rng.randint(1, 20) for _ in range(n_crates)])
        values = sorted([rng.randint(10, 100) for _ in range(n_crates)])
        base_serial = 10000000 + case_no * 100000
        for i in range(n_crates):
            cid = i + 1
            cat = rng.randint(0, 4)
            w = weights[i]
            v = values[i]
            exp = rng.randint(0, 999)
            ser = base_serial + i
            crates.append({
                'crate_id': cid,
                'cat': cat,
                'weight': w,
                'value': v,
                'expiry': exp,
                'serial': ser
            })
        total_weight = sum(c['weight'] for c in crates)
        capacity = int(round(0.35 * total_weight))
    elif case_no == 47:
        # Trap 47: Best-looking-crate trap.
        # Taking crates in decreasing order of value per kg and skipping those that do not fit
        # reaches at most 60% of the best possible total value.
        capacity = 30
        base_serial = 20000000 + case_no * 100000
        items_spec = [
            (16, 100),
            (15, 90),
            (15, 90)
        ]
        while len(items_spec) < n_crates:
            items_spec.append((15, 15))
            
        for i, (w, v) in enumerate(items_spec):
            cid = i + 1
            cat = rng.randint(0, 4)
            exp = rng.randint(0, 999)
            ser = base_serial + i
            crates.append({
                'crate_id': cid,
                'cat': cat,
                'weight': w,
                'value': v,
                'expiry': exp,
                'serial': ser
            })
        total_weight = sum(c['weight'] for c in crates)
    elif tier == 'S' and case_no < 5:
        # Variety Rule 1: In at least 5 tier-S cases, greedy by value/weight is not optimal.
        # Dynamic construction ensuring capacity / total_weight in [0.10, 0.70]
        capacity = 20
        w2 = capacity // 2 # 10
        w3 = capacity - w2 # 10
        w1 = w2 + 1        # 11
        v1 = int(w1 * 5.0) # 55
        v2 = int(w2 * 4.5) + 2 # 47
        v3 = int(w3 * 4.5) + 2 # 47
        if v2 + v3 <= v1:
            v2 += 2
            v3 += 2
        items_spec = [(w1, v1), (w2, v2), (w3, v3)]
        rem_cap = capacity - w1 # 9
        for _ in range(n_crates - 3):
            w = rng.randint(rem_cap + 1, min(20, rem_cap + 4))
            v = rng.randint(10, min(100, int(w * 2.5)))
            items_spec.append((w, v))
            
        base_serial = 30000000 + case_no * 100000
        for i, (w, v) in enumerate(items_spec):
            cid = i + 1
            cat = rng.randint(0, 4)
            exp = rng.randint(0, 999)
            ser = base_serial + i
            crates.append({
                'crate_id': cid,
                'cat': cat,
                'weight': w,
                'value': v,
                'expiry': exp,
                'serial': ser
            })
        total_weight = sum(c['weight'] for c in crates)
    else:
        # Standard generation respecting scenario signatures
        base_serial = 40000000 + case_no * 100000
        for i in range(n_crates):
            cid = i + 1
            w = rng.randint(1, 20)
            v = rng.randint(10, 100)
            exp = rng.randint(0, 999)
            ser = base_serial + i
            
            # Scenario category constraints
            if scenario == 1 and tier != 'X':
                # Delta flood: food (0) and water (1) >= 55%
                cat = rng.choice([0, 1]) if rng.random() < 0.65 else rng.choice([2, 3, 4])
            elif scenario == 2 and tier != 'X':
                # Mountain earthquake: medicine (2) and tool (3) >= 45%
                cat = rng.choice([2, 3]) if rng.random() < 0.55 else rng.choice([0, 1, 4])
            elif scenario == 4 and tier != 'X':
                # Urban flash flood: rare (4) >= 10%
                cat = 4 if rng.random() < 0.20 else rng.choice([0, 1, 2, 3])
            elif scenario == 6 and tier != 'X':
                # Outbreak camp: medicine (2) and water (1) >= 55%, >= half expire by 300
                cat = rng.choice([1, 2]) if rng.random() < 0.65 else rng.choice([0, 3, 4])
                if rng.random() < 0.60:
                    exp = rng.randint(0, 300)
            else:
                cat = rng.randint(0, 4)
                
            crates.append({
                'crate_id': cid,
                'cat': cat,
                'weight': w,
                'value': v,
                'expiry': exp,
                'serial': ser
            })
            
        total_weight = sum(c['weight'] for c in crates)
        min_cap = max(1, math.ceil(0.15 * total_weight))
        max_cap = max(min_cap, int(0.65 * total_weight))
        capacity = rng.randint(min_cap, max_cap)
            
    # Guarantee scenario signature minimums if not tier X
    if tier != 'X':
        if scenario == 1:
            fw = sum(1 for c in crates if c['cat'] in (0, 1))
            needed = math.ceil(0.55 * n_crates)
            for c in crates:
                if fw >= needed:
                    break
                if c['cat'] not in (0, 1):
                    c['cat'] = rng.choice([0, 1])
                    fw += 1
        elif scenario == 2:
            mt = sum(1 for c in crates if c['cat'] in (2, 3))
            needed = math.ceil(0.45 * n_crates)
            for c in crates:
                if mt >= needed:
                    break
                if c['cat'] not in (2, 3):
                    c['cat'] = rng.choice([2, 3])
                    mt += 1
        elif scenario == 4:
            rare = sum(1 for c in crates if c['cat'] == 4)
            needed = math.ceil(0.10 * n_crates)
            for c in crates:
                if rare >= needed:
                    break
                if c['cat'] != 4:
                    c['cat'] = 4
                    rare += 1
        elif scenario == 6:
            mw = sum(1 for c in crates if c['cat'] in (1, 2))
            needed = math.ceil(0.55 * n_crates)
            for c in crates:
                if mw >= needed:
                    break
                if c['cat'] not in (1, 2):
                    c['cat'] = rng.choice([1, 2])
                    mw += 1
            exp_300 = sum(1 for c in crates if c['expiry'] <= 300)
            needed_exp = math.ceil(0.50 * n_crates)
            for c in crates:
                if exp_300 >= needed_exp:
                    break
                if c['expiry'] > 300:
                    c['expiry'] = rng.randint(0, 300)
                    exp_300 += 1

    # Final assert on capacity
    assert 1 <= capacity <= total_weight, f"Case {case_no}: capacity {capacity} not in [1, {total_weight}]"
    assert 0.10 <= capacity / total_weight <= 0.70, f"Case {case_no}: ratio {capacity / total_weight} not in [0.10, 0.70]"

    # -------------------------------------------------------------
    # 2. LOCATIONS, ROADS & CLOSURE WAVES
    # -------------------------------------------------------------
    if tier == 'S':
        V = rng.randint(6, 12)
    elif tier == 'M':
        V = rng.randint(30, 150)
    elif tier == 'L':
        V = rng.randint(500, 2000)
    else: # tier X
        if case_no == 48: # Shortest-looks-cheapest trap
            V = rng.randint(1500, 3000)
        else:
            V = rng.randint(500, 2000)
            
    # Target degree and road counts based on scenarios
    if tier != 'X' and scenario == 1:
        avg_deg = rng.uniform(2.4, 3.0)
        E_target = int(round(avg_deg * V / 2.0))
    elif tier != 'X' and scenario == 2:
        avg_deg = rng.uniform(2.1, 2.5)
        E_target = int(round(avg_deg * V / 2.0))
    elif tier != 'X' and scenario == 4:
        avg_deg = rng.uniform(3.6, 4.2)
        E_target = int(round(avg_deg * V / 2.0))
    elif tier != 'X' and scenario == 5:
        avg_deg = rng.uniform(2.0, 2.2)
        E_target = int(round(avg_deg * V / 2.0))
    elif case_no == 48:
        avg_deg = 2.1
        E_target = int(round(avg_deg * V / 2.0))
    else:
        avg_deg = rng.uniform(2.2, 3.0)
        E_target = int(round(avg_deg * V / 2.0))
        
    E_target = max(V - 1, min(3 * V, E_target))
    
    # Generate locations
    locations = []
    # Location 0 is HQ: type D, penalty 0
    locations.append({'loc_id': 0, 'type': 'D', 'penalty': 0})
    
    for vid in range(1, V):
        if tier != 'X' and scenario == 3:
            loc_type = 'S' if rng.random() < 0.35 else rng.choice(['H', 'J', 'D'])
        else:
            loc_type = rng.choice(['S', 'H', 'J', 'D'])
            
        if tier != 'X' and scenario == 1:
            pen = rng.choice([2, 4, 6]) if rng.random() < 0.50 else rng.choice([0, 1])
        else:
            pen = rng.choice([0, 1, 2, 4, 6])
            
        locations.append({'loc_id': vid, 'type': loc_type, 'penalty': pen})
        
    # Guarantee at least one S and one H
    s_nodes = [loc for loc in locations if loc['type'] == 'S' and loc['loc_id'] != 0]
    h_nodes = [loc for loc in locations if loc['type'] == 'H' and loc['loc_id'] != 0]
    if not s_nodes:
        locations[1]['type'] = 'S'
    if not h_nodes:
        locations[2 if V > 2 else 1]['type'] = 'H'
        
    if tier != 'X' and scenario == 3:
        num_s = sum(1 for loc in locations if loc['type'] == 'S')
        needed_s = math.ceil(0.25 * V)
        for loc in locations:
            if num_s >= needed_s:
                break
            if loc['loc_id'] != 0 and loc['type'] != 'S':
                loc['type'] = 'S'
                num_s += 1
                
    if tier != 'X' and scenario == 1:
        num_pen = sum(1 for loc in locations if loc['penalty'] >= 2)
        needed_pen = math.ceil(0.40 * V)
        for loc in locations:
            if num_pen >= needed_pen:
                break
            if loc['loc_id'] != 0 and loc['penalty'] < 2:
                loc['penalty'] = rng.choice([2, 4, 6])
                num_pen += 1
                
    # Candidate targets (distinct shelters or hospitals, not HQ)
    valid_targets = [loc['loc_id'] for loc in locations if loc['loc_id'] != 0 and loc['type'] in ('S', 'H')]
    if len(valid_targets) < 3:
        for loc in locations:
            if loc['loc_id'] != 0 and loc['loc_id'] not in valid_targets:
                loc['type'] = rng.choice(['S', 'H'])
                valid_targets.append(loc['loc_id'])
                if len(valid_targets) >= 3:
                    break
                    
    target_0 = valid_targets[0]
    target_1 = valid_targets[1]
    target_2 = valid_targets[2]
    
    # Build graph edges
    edges_set = set()
    roads = []
    
    if tier != 'X' and scenario == 5:
        # Study 5: Landslide corridor
        degrees = {i: 0 for i in range(V)}
        spine_len = max(math.floor(V / 4) + 2, 3)
        for i in range(spine_len):
            u, v = i, i + 1
            edges_set.add((min(u, v), max(u, v)))
            degrees[u] += 1
            degrees[v] += 1
            
        avail_nodes = [i for i in range(spine_len + 1) if degrees[i] < 4]
        for vid in range(spine_len + 1, V):
            p = rng.choice(avail_nodes)
            edges_set.add((min(p, vid), max(p, vid)))
            degrees[p] += 1
            degrees[vid] += 1
            if degrees[p] >= 4:
                avail_nodes.remove(p)
            avail_nodes.append(vid)
    elif case_no == 48:
        # Trap 48: Longest distance between two locations >= 500 roads.
        # Min-hop cost to target_0 >= 1.5 * cheapest route cost.
        spine_len = 550
        for i in range(spine_len):
            edges_set.add((i, i + 1))
        for vid in range(spine_len + 1, V - 2):
            p = 550 if vid == spine_len + 1 else vid - 1
            edges_set.add((min(p, vid), max(p, vid)))
            
        inter_node = V - 1
        target_0 = V - 2
        locations[target_0]['type'] = 'S'
        locations[target_0]['penalty'] = 0
        locations[inter_node]['penalty'] = 0
        
        edges_set.add((min(0, target_0), max(0, target_0)))
        edges_set.add((min(0, inter_node), max(0, inter_node)))
        edges_set.add((min(inter_node, target_0), max(inter_node, target_0)))
    elif tier == 'S' and case_no <= 5:
        # Variety 2: direct edge from 0 to target_0 with high cost, 2-hop path with low cost
        inter_node = (target_0 % (V - 1)) + 1
        if inter_node == target_0:
            inter_node = ((target_0 + 1) % (V - 1)) + 1
            
        for vid in range(1, V):
            p = rng.randint(0, vid - 1)
            edges_set.add((min(p, vid), max(p, vid)))
            
        edges_set.add((min(0, target_0), max(0, target_0)))
        edges_set.add((min(0, inter_node), max(0, inter_node)))
        edges_set.add((min(inter_node, target_0), max(inter_node, target_0)))
        # Set penalties to 0
        locations[target_0]['penalty'] = 0
        locations[inter_node]['penalty'] = 0
        if tier != 'X' and scenario == 1:
            num_pen = sum(1 for loc in locations if loc['penalty'] >= 2)
            needed_pen = math.ceil(0.40 * V)
            for loc in locations:
                if num_pen >= needed_pen:
                    break
                if loc['loc_id'] not in (0, target_0, inter_node) and loc['penalty'] < 2:
                    loc['penalty'] = 2
                    num_pen += 1
    else:
        for vid in range(1, V):
            p = rng.randint(0, vid - 1)
            edges_set.add((min(p, vid), max(p, vid)))
            
    # Add random extra edges up to E_target while satisfying constraints
    if tier != 'X' and scenario == 5:
        tree_adj = {i: [] for i in range(V)}
        for eu, ev in edges_set:
            tree_adj[eu].append(ev)
            tree_adj[ev].append(eu)
        dist_0 = {0: 0}
        q = deque([0])
        while q:
            curr = q.popleft()
            for nxt in tree_adj[curr]:
                if nxt not in dist_0:
                    dist_0[nxt] = dist_0[curr] + 1
                    q.append(nxt)

        all_pairs = []
        for u in range(V):
            for v in range(u + 1, V):
                if (u, v) not in edges_set and degrees[u] < 4 and degrees[v] < 4:
                    if abs(dist_0[u] - dist_0[v]) <= 1:
                        all_pairs.append((u, v))
        rng.shuffle(all_pairs)
        for u, v in all_pairs:
            if len(edges_set) >= E_target:
                break
            if degrees[u] < 4 and degrees[v] < 4:
                edges_set.add((u, v))
                degrees[u] += 1
                degrees[v] += 1
    else:
        if V <= 50:
            all_pairs = []
            for u in range(V):
                for v in range(u + 1, V):
                    if (u, v) not in edges_set:
                        all_pairs.append((u, v))
            rng.shuffle(all_pairs)
            for pair in all_pairs:
                if len(edges_set) >= E_target:
                    break
                edges_set.add(pair)
        elif case_no == 48:
            attempts = 0
            while len(edges_set) < E_target and attempts < 10 * E_target:
                attempts += 1
                u = rng.randint(550, V - 3)
                v = rng.randint(550, V - 3)
                if u != v:
                    edges_set.add((min(u, v), max(u, v)))
        else:
            attempts = 0
            while len(edges_set) < E_target and attempts < 10 * E_target:
                attempts += 1
                u = rng.randint(0, V - 2)
                v = rng.randint(u + 1, V - 1)
                edges_set.add((u, v))

    sorted_edges = sorted(list(edges_set))
    if case_no == 48:
        inter_node = V - 1 if target_0 != V - 1 else V - 2
    else:
        inter_node = (target_0 % (V - 1)) + 1
        if inter_node == target_0:
            inter_node = ((target_0 + 1) % (V - 1)) + 1

    for r_idx, (u, v) in enumerate(sorted_edges):
        minutes = rng.randint(5, 40)
        cable = rng.randint(1, 100)
        
        # Tuning for Variety 2 and Trap 48
        if tier == 'S' and case_no <= 5:
            if (u, v) == (min(0, target_0), max(0, target_0)):
                minutes = 55
            elif (u, v) in ((min(0, inter_node), max(0, inter_node)),
                            (min(inter_node, target_0), max(inter_node, target_0))):
                minutes = 2
        elif case_no == 48:
            if (u, v) == (min(0, target_0), max(0, target_0)):
                minutes = 60
            elif (u, v) in ((min(0, inter_node), max(0, inter_node)),
                            (min(inter_node, target_0), max(inter_node, target_0))):
                minutes = 2
                
        roads.append({
            'road_no': r_idx,
            'u': u,
            'v': v,
            'minutes': minutes,
            'cable': cable
        })

    E = len(roads)
    # Check degree constraints
    avg_degree = (2.0 * E) / V
    if tier != 'X':
        if scenario == 1:
            assert 2.2 <= avg_degree <= 3.2, f"Case {case_no}: avg degree {avg_degree} not in [2.2, 3.2]"
        elif scenario == 2:
            assert 2.0 <= avg_degree <= 2.6, f"Case {case_no}: avg degree {avg_degree} not in [2.0, 2.6]"
        elif scenario == 4:
            assert avg_degree >= 3.5, f"Case {case_no}: avg degree {avg_degree} < 3.5"
        elif scenario == 5:
            assert avg_degree <= 2.4, f"Case {case_no}: avg degree {avg_degree} > 2.4"
            for node in range(V):
                deg = sum(1 for r in roads if r['u'] == node or r['v'] == node)
                assert deg <= 4, f"Case {case_no}: node {node} has deg {deg} > 4"

    # Closure waves
    if tier != 'X' and scenario in (1, 3, 5):
        num_waves = rng.randint(3, 5)
    else:
        num_waves = rng.randint(2, 5)
        
    max_roads_per_wave = max(1, math.floor(E / 4))
    waves = []
    used_roads = set()
    
    if tier != 'X' and scenario == 5:
        # Union of all waves leaves at least one target unreachable from HQ
        incident_to_target = [r['road_no'] for r in roads if r['u'] == target_0 or r['v'] == target_0]
        wave_roads = {w: [] for w in range(num_waves)}
        for idx, r_no in enumerate(incident_to_target):
            w_idx = idx % num_waves
            wave_roads[w_idx].append(r_no)
            used_roads.add(r_no)
            
        other_roads = [r['road_no'] for r in roads if r['road_no'] not in used_roads]
        rng.shuffle(other_roads)
        for w in range(num_waves):
            while len(wave_roads[w]) < max_roads_per_wave and other_roads:
                r_pick = other_roads.pop()
                wave_roads[w].append(r_pick)
                used_roads.add(r_pick)
                if len(wave_roads[w]) >= 1 and rng.random() < 0.4:
                    break
            if not wave_roads[w] and other_roads:
                r_pick = other_roads.pop()
                wave_roads[w].append(r_pick)
                used_roads.add(r_pick)
                
        for w in range(num_waves):
            for r_no in sorted(wave_roads[w]):
                waves.append({'wave_no': w, 'road_no': r_no})
    else:
        all_road_indices = list(range(E))
        rng.shuffle(all_road_indices)
        for w in range(num_waves):
            size = rng.randint(1, max_roads_per_wave)
            wave_list = []
            while len(wave_list) < size and all_road_indices:
                r_pick = all_road_indices.pop()
                wave_list.append(r_pick)
            for r_no in sorted(wave_list):
                waves.append({'wave_no': w, 'road_no': r_no})

    waves.sort(key=lambda x: (x['wave_no'], x['road_no']))

    # -------------------------------------------------------------
    # 3. RADIO LOG, PATTERNS & REPORTS
    # -------------------------------------------------------------
    if tier == 'S':
        log_len = rng.randint(200, 500)
    elif tier == 'M':
        log_len = rng.randint(2000, 10000)
    elif tier == 'L':
        log_len = rng.randint(20000, 100000)
    else: # tier X
        if case_no == 49: # Near-miss trap
            log_len = rng.randint(50000, 100000)
        else:
            log_len = rng.randint(20000, 100000)
            
    if case_no == 49:
        num_a = int(0.96 * log_len)
        rem = log_len - num_a
        raw_log = 'A' * num_a + ''.join(rng.choices(ALPHABET_38, k=rem))
    elif tier != 'X' and scenario == 3:
        chosen_symbols = rng.sample(ALPHABET_38, k=rng.randint(32, 38))
        raw_log = ''.join(rng.choices(chosen_symbols, k=log_len))
        for i, sym in enumerate(chosen_symbols[:32]):
            raw_log = raw_log[:i] + sym + raw_log[i+1:]
    elif tier != 'X' and scenario == 6:
        dom_sym = rng.choice(ALPHABET_38)
        num_dom = int(0.30 * log_len)
        rem = log_len - num_dom
        dom_chars = [dom_sym] * num_dom + rng.choices(ALPHABET_38, k=rem)
        rng.shuffle(dom_chars)
        raw_log = ''.join(dom_chars)
    else:
        raw_log = ''.join(rng.choices(ALPHABET_38, k=log_len))

    radio_log_parts = []
    chunk_size = 10000
    for p_idx, start_pos in enumerate(range(0, len(raw_log), chunk_size), start=1):
        radio_log_parts.append({
            'part': p_idx,
            'text': raw_log[start_pos:start_pos + chunk_size]
        })
        
    pattern_lengths = [2, 4, 8, 12, 20, 40]
    radio_patterns = []
    
    if case_no == 49:
        p0 = 'AA'
        p1 = 'AAAA'
        p2 = 'A' * 7 + 'B'
        p3 = 'A' * 11 + 'B'
        p4 = ''.join(rng.choices(ALPHABET_38, k=20))
        p5 = '-' * 40
        p_candidates = [p0, p1, p2, p3, p4, p5]
    else:
        p0 = raw_log[:2]
        p1 = raw_log[5:9] if len(raw_log) > 9 else raw_log[:4]
        p2 = ''.join(rng.choices(ALPHABET_38, k=8))
        p3 = ''.join(rng.choices(ALPHABET_38, k=12))
        p4 = ''.join(rng.choices(ALPHABET_38, k=20))
        p5 = 'Q_Z_9-9-Z_Q' * 4
        p5 = p5[:40]
        p_candidates = [p0, p1, p2, p3, p4, p5]

    for p_no, (plen, p_str) in enumerate(zip(pattern_lengths, p_candidates)):
        cnt = count_overlapping_occurrences(raw_log, p_str)
        radio_patterns.append({
            'pattern_no': p_no,
            'pattern': p_str,
            'count': cnt
        })
        
    occ_count = sum(1 for p in radio_patterns if p['count'] > 0)
    zero_count = sum(1 for p in radio_patterns if p['count'] == 0)
    if occ_count < 2 or zero_count < 1:
        p0 = raw_log[:2]
        radio_patterns[0]['pattern'] = p0
        radio_patterns[0]['count'] = count_overlapping_occurrences(raw_log, p0)
        p1 = raw_log[2:6]
        radio_patterns[1]['pattern'] = p1
        radio_patterns[1]['count'] = count_overlapping_occurrences(raw_log, p1)
        p5 = '~~~NOT_PRESENT~~~'[:40].replace('~', '_')
        while count_overlapping_occurrences(raw_log, p5) > 0:
            p5 = ''.join(rng.choices(['-', '_'], k=40))
        radio_patterns[5]['pattern'] = p5
        radio_patterns[5]['count'] = 0

    if tier == 'S':
        min_rep_len, max_rep_len = 10, 30
    elif tier == 'M':
        min_rep_len, max_rep_len = 30, 150
    else: # tier L / X
        min_rep_len, max_rep_len = 200, 1000
        
    rep_len = rng.randint(min_rep_len, max_rep_len)
    rep_a = ''.join(rng.choices(ALPHABET_38, k=rep_len))
    rep_b_chars = list(rep_a)
    num_mutations = max(1, int(rep_len * 0.15))
    for _ in range(num_mutations):
        op = rng.choice(['ins', 'del', 'sub'])
        pos = rng.randint(0, len(rep_b_chars) - 1) if rep_b_chars else 0
        if op == 'sub' and rep_b_chars:
            rep_b_chars[pos] = rng.choice(ALPHABET_38)
        elif op == 'del' and len(rep_b_chars) > min_rep_len:
            rep_b_chars.pop(pos)
        elif op == 'ins' and len(rep_b_chars) < max_rep_len:
            rep_b_chars.insert(pos, rng.choice(ALPHABET_38))
    rep_b = ''.join(rep_b_chars)
    
    true_lev = levenshtein_distance(rep_a, rep_b)
    edit_bound = true_lev
    assert true_lev <= edit_bound <= (len(rep_a) + len(rep_b))

    # -------------------------------------------------------------
    # 4. WINDOWS
    # -------------------------------------------------------------
    if tier == 'S':
        n_windows = rng.randint(8, 20)
    elif tier == 'M':
        n_windows = rng.randint(50, 300)
    else: # tier L / X
        n_windows = rng.randint(1000, 3000)
        
    windows = []
    
    if tier != 'X' and scenario == 3:
        cluster_starts = [rng.randint(0, 1000) for _ in range(5)]
        for wid in range(1, n_windows + 1):
            base_s = rng.choice(cluster_starts)
            dur = rng.randint(80, 300)
            s = max(0, min(1440 - dur, base_s + rng.randint(-30, 30)))
            f = s + dur
            val = rng.randint(1, 100)
            windows.append({'window_id': wid, 'start': s, 'finish': f, 'value': val})
    else:
        for wid in range(1, n_windows + 1):
            dur = rng.randint(5, 480)
            s = rng.randint(0, 1440 - dur)
            f = s + dur
            val = rng.randint(1, 100)
            windows.append({'window_id': wid, 'start': s, 'finish': f, 'value': val})
            
    if n_windows >= 8:
        dur0 = rng.randint(5, 200)
        s0 = rng.randint(0, 800)
        windows[0]['start'] = s0
        windows[0]['finish'] = s0 + dur0
        dur1 = rng.randint(5, min(480, 1440 - windows[0]['finish']))
        windows[1]['start'] = windows[0]['finish']
        windows[1]['finish'] = windows[0]['finish'] + dur1

        dur2 = rng.randint(5, 200)
        s2 = rng.randint(0, 800)
        windows[2]['start'] = s2
        windows[2]['finish'] = s2 + dur2
        dur3 = rng.randint(5, min(480, 1440 - windows[2]['finish']))
        windows[3]['start'] = windows[2]['finish']
        windows[3]['finish'] = windows[2]['finish'] + dur3

    # -------------------------------------------------------------
    # 5. INCIDENTS (ALARMS)
    # -------------------------------------------------------------
    if tier == 'S':
        n_alarms = rng.randint(10, 40)
    elif tier == 'M':
        n_alarms = rng.randint(200, 1000)
    else: # tier L / X
        n_alarms = rng.randint(2000, 5000)
        
    incidents = []
    
    if tier in ('M', 'L'):
        if scenario == 4 and tier != 'X':
            rate = rng.uniform(1.52, 1.78)
        else:
            rate = rng.uniform(1.22, 1.48)
            
        target_last_tick = max(1, int(round(n_alarms / rate)) - 1)
        ticks = [0]
        for i in range(1, n_alarms):
            t = int(round((i / (n_alarms - 1)) * target_last_tick))
            ticks.append(t)
        ticks[0] = 0
        ticks[-1] = target_last_tick
    else:
        ticks = [0]
        for _ in range(n_alarms - 1):
            ticks.append(ticks[-1] + (1 if rng.random() < 0.6 else 0))
            
    priorities = []
    for _ in range(n_alarms):
        if tier != 'X' and scenario == 2:
            p = rng.choices([1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                            weights=[1, 1, 2, 2, 3, 5, 8, 12, 15, 20])[0]
        else:
            p = rng.randint(1, 10)
        priorities.append(p)
        
    if tier in ('M', 'L'):
        must_haves = [1, 2, 3, 4, 5, 6]
        for idx, mh in enumerate(must_haves):
            priorities[idx] = mh
            
    if tier != 'X' and scenario == 2:
        while (sum(priorities) / len(priorities)) < 6.05:
            idx = rng.randint(0, n_alarms - 1)
            priorities[idx] = 10

    for aid in range(1, n_alarms + 1):
        incidents.append({
            'alarm_id': aid,
            'tick': ticks[aid - 1],
            'priority': priorities[aid - 1]
        })

    # -------------------------------------------------------------
    # 6. SITES & PLANTED TOUR
    # -------------------------------------------------------------
    if tier == 'S':
        n_sites = rng.randint(5, 9)
    elif tier == 'M':
        n_sites = rng.randint(10, 16)
    else: # tier L / X
        n_sites = rng.randint(200, 500)
        
    sites_coords = []
    used_pts = set()
    for s_no in range(n_sites):
        while True:
            pt = (rng.randint(0, 999), rng.randint(0, 999))
            if pt not in used_pts:
                used_pts.add(pt)
                sites_coords.append(pt)
                break
                
    sites = [{'site_no': i, 'x': pt[0], 'y': pt[1]} for i, pt in enumerate(sites_coords)]
    nn_len, nn_tour_order = nearest_neighbor_tour_length(sites_coords)
    planted_tour = nn_tour_order
    tour_len = nn_len
        
    tour_rows = []
    for step, s_no in enumerate(planted_tour):
        tour_rows.append({'step': step, 'site_no': s_no})

    # -------------------------------------------------------------
    # 7. PIPELINE DIMS
    # -------------------------------------------------------------
    if tier == 'S':
        n_pipeline = rng.randint(4, 8)
    elif tier == 'M':
        n_pipeline = rng.randint(15, 60)
    else: # tier L / X
        n_pipeline = rng.randint(100, 300)
        
    pipeline_dims = []
    for idx in range(n_pipeline + 1):
        pipeline_dims.append({'idx': idx, 'dim': rng.randint(2, 100)})

    # -------------------------------------------------------------
    # 8. DRUM PRICES
    # -------------------------------------------------------------
    if tier == 'S':
        drum_len = rng.randint(5, 14)
    elif tier == 'M':
        drum_len = rng.randint(40, 200)
    else: # tier L / X
        drum_len = rng.randint(500, 2000)
        
    drum_prices = []
    base_rate = rng.randint(2, 10)
    for j in range(1, drum_len + 1):
        noise = rng.randint(-3, 8)
        p = max(1, min(500, int(round(j * base_rate + noise))))
        drum_prices.append({'length': j, 'price': p})
    if len(drum_prices) >= 2:
        drum_prices[-1]['price'] = min(500, drum_prices[-1]['price'] + 7)

    # -------------------------------------------------------------
    # 9. SENSOR EDGES & COVER
    # -------------------------------------------------------------
    if tier == 'S':
        n_sensors = rng.randint(6, 14)
    elif tier == 'M':
        n_sensors = rng.randint(20, 40)
    else: # tier L / X
        n_sensors = rng.randint(100, 400)
        
    sensor_k = rng.randint(2, max(2, n_sensors // 2))
    planted_cover = sorted(rng.sample(range(n_sensors), k=sensor_k))
    cover_set = set(planted_cover)
    
    sensor_edges_set = set()
    non_cover = [node for node in range(n_sensors) if node not in cover_set]
    for nc in non_cover:
        c_node = rng.choice(planted_cover)
        sensor_edges_set.add((min(nc, c_node), max(nc, c_node)))
        
    for i in range(len(planted_cover) - 1):
        u = planted_cover[i]
        v = planted_cover[i + 1]
        sensor_edges_set.add((min(u, v), max(u, v)))
        
    target_sensor_edges = max(n_sensors - 1, int(1.3 * n_sensors))
    attempts = 0
    while len(sensor_edges_set) < target_sensor_edges and attempts < 10 * target_sensor_edges:
        attempts += 1
        u = rng.choice(planted_cover)
        v = rng.randint(0, n_sensors - 1)
        if u != v:
            sensor_edges_set.add((min(u, v), max(u, v)))
            
    sensor_edges = []
    for u, v in sorted(list(sensor_edges_set)):
        sensor_edges.append({'u': u, 'v': v})
        
    sensor_cover = [{'node': node} for node in planted_cover]

    # -------------------------------------------------------------
    # 10. SAFETY RULES & PLANTED ASSIGNMENT
    # -------------------------------------------------------------
    if tier == 'S':
        safety_vars = rng.randint(6, 15)
        rules_ratio = rng.uniform(2.5, 5.5)
    elif tier in ('M', 'L'):
        safety_vars = rng.randint(20, 50)
        if 20 <= case_no <= 25:
            rules_ratio = rng.uniform(2.6, 3.2)
        elif 26 <= case_no <= 37:
            rules_ratio = rng.uniform(3.7, 4.6)
        else:
            rules_ratio = rng.uniform(4.9, 5.8)
    else: # tier X
        safety_vars = rng.randint(20, 50)
        rules_ratio = rng.uniform(3.0, 5.0)
        
    num_safety_rules = max(int(round(rules_ratio * safety_vars)), 3 * safety_vars // 2)
    planted_switches = {sw: rng.choice([0, 1]) for sw in range(1, safety_vars + 1)}
    
    safety_rules = []
    for r_no in range(1, num_safety_rules + 1):
        vars_3 = rng.sample(range(1, safety_vars + 1), k=3)
        val1 = planted_switches[vars_3[0]]
        lit1 = vars_3[0] if val1 == 1 else -vars_3[0]
        lit2 = vars_3[1] if rng.random() < 0.5 else -vars_3[1]
        lit3 = vars_3[2] if rng.random() < 0.5 else -vars_3[2]
        
        lits = [lit1, lit2, lit3]
        rng.shuffle(lits)
        safety_rules.append({
            'rule_no': r_no,
            'lit_1': lits[0],
            'lit_2': lits[1],
            'lit_3': lits[2]
        })
        
    safety_planted = [{'switch': sw, 'value': val} for sw, val in sorted(planted_switches.items())]

    # -------------------------------------------------------------
    # 11. RATIONS
    # -------------------------------------------------------------
    if tier == 'S':
        n_rations = rng.randint(8, 20)
    elif tier == 'M':
        n_rations = rng.randint(24, 40)
    else: # tier L / X
        n_rations = rng.randint(50, 100)
        
    rations = []
    planted_count = rng.randint(2, max(2, n_rations // 2))
    planted_indices = set(rng.sample(range(n_rations), k=planted_count))
    
    rations_target = 0
    for it in range(n_rations):
        val = rng.randint(1, 1000)
        is_pl = 1 if it in planted_indices else 0
        if is_pl:
            rations_target += val
        rations.append({
            'item': it,
            'value': val,
            'planted': is_pl
        })
    assert rations_target > 0

    # -------------------------------------------------------------
    # 12. CLAIMS (TIER S ONLY)
    # -------------------------------------------------------------
    claims_row = None
    if tier == 'S':
        crate_weights = [c['weight'] for c in crates]
        crate_values = [c['value'] for c in crates]
        cargo_opt = solve_knapsack(capacity, crate_weights, crate_values)
        
        win_tuples = [(w['start'], w['finish'], w['value']) for w in windows]
        window_count_opt = solve_interval_scheduling_count(win_tuples)
        window_value_opt = solve_interval_scheduling_weight(win_tuples)
        
        price_dict = {p['length']: p['price'] for p in drum_prices}
        drum_opt = solve_rod_cutting(price_dict, drum_len)
        tour_opt = solve_tsp_manhattan(sites_coords)
        
        edge_tuples = [(e['u'], e['v']) for e in sensor_edges]
        cover_min = solve_min_vertex_cover(n_sensors, edge_tuples)
        
        claims_row = {
            'case_id': case_id,
            'cargo_opt': cargo_opt,
            'window_count_opt': window_count_opt,
            'window_value_opt': window_value_opt,
            'drum_opt': drum_opt,
            'tour_opt': tour_opt,
            'cover_min': cover_min
        }

    cases_row = {
        'case_id': case_id,
        'group_seed': seed,
        'case_no': case_no,
        'tier': tier,
        'scenario': scenario,
        'capacity': capacity,
        'target_0': target_0,
        'target_1': target_1,
        'target_2': target_2,
        'edit_bound': edit_bound,
        'tour_length': tour_len,
        'sensor_nodes': n_sensors,
        'sensor_k': sensor_k,
        'safety_vars': safety_vars,
        'rations_target': rations_target
    }

    return {
        'case_id': case_id,
        'cases': cases_row,
        'crates': crates,
        'locations': locations,
        'roads': roads,
        'waves': waves,
        'radio_log': radio_log_parts,
        'radio_patterns': radio_patterns,
        'radio_reports': [{'case_id': case_id, 'report_a': rep_a, 'report_b': rep_b}],
        'windows': windows,
        'incidents': incidents,
        'sites': sites,
        'tour': tour_rows,
        'pipeline_dims': pipeline_dims,
        'drum_prices': drum_prices,
        'sensor_edges': sensor_edges,
        'sensor_cover': sensor_cover,
        'safety_rules': safety_rules,
        'safety_planted': safety_planted,
        'rations': rations,
        'claims': claims_row
    }
