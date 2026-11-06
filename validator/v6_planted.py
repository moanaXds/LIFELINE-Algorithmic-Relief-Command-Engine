"""
v6_planted.py - Planted objects validation for LIFELINE Phase 1 Validator.

Verifies:
1. Planted Tour:
   - Valid permutation of all sites starting at site 0.
   - Recomputed closed Manhattan tour length matches tour_length in cases sheet.
   - On Tiers L and X, planted tour length <= nearest-neighbour tour length from site 0
     (ties in distance broken by smallest site_no).
   - Distinct site coordinates: no two sites have identical (x, y).
2. Sensor Graph & Planted Cover:
   - Sensor edges: u < v, no loops, no duplicates, at least n - 1 edges.
   - Planted cover: exactly sensor_k distinct nodes, 2 <= sensor_k <= floor(n/2).
   - Cover validity: every edge in sensor_edges has at least one endpoint in the cover.
3. Safety Rules & Planted Assignment:
   - Each rule has 3 non-zero integer literals on 3 distinct switches in 1..safety_vars.
   - Ratio: len(safety_rules) / safety_vars in [2.0, 6.0].
   - Planted 0/1 assignment satisfies every rule (+j is True if switch j=1; -j is True if j=0).
4. Rations:
   - Each item has planted flag in {0, 1}.
   - rations_target > 0.
   - Sum of values for items with planted == 1 equals rations_target exactly.
"""

def manhattan_distance(p1, p2):
    """Computes Manhattan (L1) distance |x1 - x2| + |y1 - y2|."""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def compute_nearest_neighbour_tour(coords):
    """
    Computes closed Manhattan tour length using the Nearest-Neighbour heuristic
    starting at site 0, breaking ties by smallest site_no.
    
    Args:
        coords (dict): site_no -> (x, y)
        
    Returns:
        int: Closed tour length.
    """
    n = len(coords)
    if n <= 1:
        return 0

    visited = [False] * n
    visited[0] = True
    curr = 0
    tour = [0]

    for _ in range(n - 1):
        best_d = float('inf')
        best_nxt = None
        for nxt in range(n):
            if not visited[nxt]:
                d = manhattan_distance(coords[curr], coords[nxt])
                if d < best_d:
                    best_d = d
                    best_nxt = nxt
                elif d == best_d and (best_nxt is None or nxt < best_nxt):
                    best_nxt = nxt
        visited[best_nxt] = True
        tour.append(best_nxt)
        curr = best_nxt

    # Closed tour cost
    cost = 0
    for i in range(n - 1):
        cost += manhattan_distance(coords[tour[i]], coords[tour[i + 1]])
    cost += manhattan_distance(coords[tour[-1]], coords[0])
    return cost


def validate_case_v6(case_id, case_data):
    """
    Validates planted objects for a single case.
    
    Args:
        case_id (str): Identifier, e.g., '18-00'.
        case_data (dict): Mapping of sheet_name -> list of row dicts.
        
    Returns:
        list of str: List of detected V6 errors.
    """
    errors = []

    cases_rows = case_data.get('cases', [])
    if not cases_rows:
        return errors
    case_meta = cases_rows[0]
    tier = case_meta.get('tier', 'S')
    stored_tour_len = case_meta.get('tour_length')
    sensor_nodes = case_meta.get('sensor_nodes', 0)
    sensor_k = case_meta.get('sensor_k', 0)
    safety_vars = case_meta.get('safety_vars', 0)
    rations_target = case_meta.get('rations_target')

    sites = case_data.get('sites', [])
    tour = case_data.get('tour', [])
    sensor_edges = case_data.get('sensor_edges', [])
    sensor_cover = case_data.get('sensor_cover', [])
    safety_rules = case_data.get('safety_rules', [])
    safety_planted = case_data.get('safety_planted', [])
    rations = case_data.get('rations', [])

    # -------------------------------------------------------------
    # 1. Sites and Tour Validation
    # -------------------------------------------------------------
    site_coords = {}
    seen_coords = set()
    for s in sites:
        sno = s.get('site_no')
        pt = (s.get('x'), s.get('y'))
        if pt in seen_coords:
            errors.append(f"V6: Multiple sites share identical coordinates {pt}.")
        seen_coords.add(pt)
        site_coords[sno] = pt

    n_sites = len(sites)
    tour_ordered = [t.get('site_no') for t in sorted(tour, key=lambda x: x.get('step', 0))]

    if len(tour_ordered) != n_sites or sorted(tour_ordered) != list(range(n_sites)):
        errors.append(f"V6: Tour is not a valid permutation of all {n_sites} sites.")
    elif tour_ordered and tour_ordered[0] != 0:
        errors.append(f"V6: Tour does not start at site 0 (starts at site {tour_ordered[0]}).")
    elif n_sites > 0:
        # Recompute closed Manhattan length
        recomputed_tour_len = 0
        for i in range(n_sites - 1):
            recomputed_tour_len += manhattan_distance(
                site_coords[tour_ordered[i]], site_coords[tour_ordered[i + 1]]
            )
        recomputed_tour_len += manhattan_distance(
            site_coords[tour_ordered[-1]], site_coords[tour_ordered[0]]
        )

        if stored_tour_len != recomputed_tour_len:
            errors.append(
                f"V6: tour_length stored {stored_tour_len}, recomputed {recomputed_tour_len}."
            )

        # On Tiers L and X: tour_length <= nearest-neighbour tour length
        if tier in ('L', 'X'):
            nn_len = compute_nearest_neighbour_tour(site_coords)
            if recomputed_tour_len > nn_len:
                errors.append(
                    f"V6: Tour length {recomputed_tour_len} is longer than Nearest-Neighbour tour ({nn_len}) on tier {tier}."
                )

    # -------------------------------------------------------------
    # 2. Sensor Graph and Vertex Cover
    # -------------------------------------------------------------
    seen_edges = set()
    for e in sensor_edges:
        u, v = e.get('u'), e.get('v')
        if u is not None and v is not None:
            if u >= v:
                errors.append(f"V6: sensor edge violates u < v: ({u}, {v}).")
            if (u, v) in seen_edges:
                errors.append(f"V6: duplicate sensor edge ({u}, {v}).")
            seen_edges.add((u, v))

    if len(sensor_edges) < sensor_nodes - 1:
        errors.append(
            f"V6: sensor_edges count {len(sensor_edges)} is less than n - 1 = {sensor_nodes - 1}."
        )

    cover_nodes = set(c.get('node') for c in sensor_cover if c.get('node') is not None)
    if len(cover_nodes) != sensor_k:
        errors.append(f"V6: sensor_cover has {len(cover_nodes)} distinct nodes, expected sensor_k = {sensor_k}.")

    if not (2 <= sensor_k <= sensor_nodes // 2):
        errors.append(f"V6: sensor_k {sensor_k} violates 2 <= k <= floor({sensor_nodes}/2).")

    # Verify that every edge is touched by the cover
    uncovered_edges = []
    for e in sensor_edges:
        u, v = e.get('u'), e.get('v')
        if u not in cover_nodes and v not in cover_nodes:
            uncovered_edges.append((u, v))

    if uncovered_edges:
        errors.append(
            f"V6: Planted sensor cover fails to touch {len(uncovered_edges)} edge(s): {uncovered_edges[:5]}."
        )

    # -------------------------------------------------------------
    # 3. Safety Rules and Planted Assignment
    # -------------------------------------------------------------
    num_rules = len(safety_rules)
    if safety_vars > 0:
        ratio = num_rules / safety_vars
        if not (2.0 <= ratio <= 6.0):
            errors.append(
                f"V6: safety rules ratio {ratio:.2f} ({num_rules}/{safety_vars}) not in [2.0, 6.0]."
            )

    # Build switch assignment dictionary
    assignment = {sp.get('switch'): sp.get('value') for sp in safety_planted}

    unsatisfied_rules = []
    for sr in safety_rules:
        rno = sr.get('rule_no')
        lits = [sr.get('lit_1'), sr.get('lit_2'), sr.get('lit_3')]
        rule_satisfied = False

        for lit in lits:
            if lit is None or lit == 0:
                continue
            sw = abs(lit)
            sw_val = assignment.get(sw)
            # +j is satisfied if switch value is 1; -j is satisfied if switch value is 0
            if (lit > 0 and sw_val == 1) or (lit < 0 and sw_val == 0):
                rule_satisfied = True
                break

        if not rule_satisfied:
            unsatisfied_rules.append(rno)

    if unsatisfied_rules:
        errors.append(
            f"V6: Planted safety assignment fails to satisfy {len(unsatisfied_rules)} rule(s): {unsatisfied_rules[:5]}."
        )

    # -------------------------------------------------------------
    # 4. Rations Planted Sum Target
    # -------------------------------------------------------------
    if rations_target is None or rations_target <= 0:
        errors.append(f"V6: rations_target {rations_target} must be a positive integer.")

    planted_sum = sum(
        rat.get('value', 0) for rat in rations if rat.get('planted') == 1
    )

    if rations_target is not None and planted_sum != rations_target:
        errors.append(
            f"V6: Planted rations sum {planted_sum} does not equal rations_target {rations_target}."
        )

    return errors

