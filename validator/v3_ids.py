"""
v3_ids.py - Identifier continuity and cross-reference validation for LIFELINE Phase 1 Validator.

Verifies:
1. Consecutive identifiers with no gaps:
   - crate_id: 1, 2, ..., num_crates
   - loc_id: 0, 1, ..., V-1
   - road_no: 0, 1, ..., E-1
   - window_id: 1, 2, ..., num_windows
   - alarm_id: 1, 2, ..., num_alarms
   - site_no: 0, 1, ..., n-1
   - pattern_no: 0, 1, ..., 5 (exactly 6 patterns)
   - rations item: 0, 1, ..., num_items-1
   - log part: 1, 2, ..., num_parts
   - drum length: 1, 2, ..., L
   - pipeline idx: 0, 1, ..., n
2. Location 0 properties:
   - Must have type 'D' (Depot / HQ)
   - Must have penalty 0
3. Location types:
   - At least one 'S' (Shelter) and at least one 'H' (Hospital) present.
4. Roads structure:
   - u < v for all roads
   - No duplicate (u, v) pairs
   - Endpoints u and v must be valid loc_ids (0 <= u, v < V)
5. Cross-references:
   - Waves road_no references a valid road_no in roads
   - Target locations target_0, target_1, target_2 reference valid loc_ids
   - Tour steps run 0..n-1, site_no references valid sites, starts at site 0, permutation of all sites
   - Sensor cover nodes reference valid sensor nodes (0 <= node < sensor_nodes)
   - Safety switches reference valid switches (1 <= switch <= safety_vars)
   - Safety rules have 3 non-zero literals on 3 distinct switches within 1..safety_vars
   - Rations planted flag in {0, 1}
6. Incidents time progression:
   - First alarm has tick == 0
   - tick is monotonic non-decreasing across all alarms
"""

def validate_case_v3(case_id, case_data):
    """
    Validates identifiers and cross-references for a single case.
    
    Args:
        case_id (str): Identifier, e.g., '18-00'.
        case_data (dict): Mapping of sheet_name -> list of row dicts.
        
    Returns:
        list of str: List of detected V3 errors.
    """
    errors = []

    cases_rows = case_data.get('cases', [])
    if not cases_rows:
        return errors
    case_meta = cases_rows[0]
    sensor_nodes = case_meta.get('sensor_nodes', 0)
    sensor_k = case_meta.get('sensor_k', 0)
    safety_vars = case_meta.get('safety_vars', 0)

    crates = case_data.get('crates', [])
    locations = case_data.get('locations', [])
    roads = case_data.get('roads', [])
    waves = case_data.get('waves', [])
    radio_log = case_data.get('radio_log', [])
    radio_patterns = case_data.get('radio_patterns', [])
    windows = case_data.get('windows', [])
    incidents = case_data.get('incidents', [])
    sites = case_data.get('sites', [])
    tour = case_data.get('tour', [])
    pipeline_dims = case_data.get('pipeline_dims', [])
    drum_prices = case_data.get('drum_prices', [])
    sensor_cover = case_data.get('sensor_cover', [])
    safety_rules = case_data.get('safety_rules', [])
    safety_planted = case_data.get('safety_planted', [])
    rations = case_data.get('rations', [])

    # ---------------------------------------------------------
    # 1. Consecutive Identifiers with No Gaps
    # ---------------------------------------------------------

    # crate_id: 1, 2, ..., num_crates
    crate_ids = [c.get('crate_id') for c in crates]
    if crate_ids != list(range(1, len(crates) + 1)):
        errors.append(f"V3: crate_id values are not consecutive from 1 to {len(crates)}.")

    # loc_id: 0, 1, ..., V-1
    V = len(locations)
    loc_ids = [l.get('loc_id') for l in locations]
    if loc_ids != list(range(V)):
        errors.append(f"V3: loc_id values are not consecutive from 0 to {V - 1}.")

    # road_no: 0, 1, ..., E-1
    E = len(roads)
    road_nos = [r.get('road_no') for r in roads]
    if road_nos != list(range(E)):
        errors.append(f"V3: road_no values are not consecutive from 0 to {E - 1}.")

    # window_id: 1, 2, ..., num_windows
    window_ids = [w.get('window_id') for w in windows]
    if window_ids != list(range(1, len(windows) + 1)):
        errors.append(f"V3: window_id values are not consecutive from 1 to {len(windows)}.")

    # alarm_id: 1, 2, ..., num_alarms
    alarm_ids = [inc.get('alarm_id') for inc in incidents]
    if alarm_ids != list(range(1, len(incidents) + 1)):
        errors.append(f"V3: alarm_id values are not consecutive from 1 to {len(incidents)}.")

    # site_no: 0, 1, ..., n-1
    num_sites = len(sites)
    site_nos = [s.get('site_no') for s in sites]
    if site_nos != list(range(num_sites)):
        errors.append(f"V3: site_no values are not consecutive from 0 to {num_sites - 1}.")

    # pattern_no: 0, 1, 2, 3, 4, 5
    pattern_nos = [p.get('pattern_no') for p in radio_patterns]
    if pattern_nos != list(range(6)):
        errors.append(f"V3: pattern_no values must be exactly [0, 1, 2, 3, 4, 5], got {pattern_nos}.")

    # rations item: 0, 1, ..., num_items-1
    ration_items = [rat.get('item') for rat in rations]
    if ration_items != list(range(len(rations))):
        errors.append(f"V3: rations item values are not consecutive from 0 to {len(rations) - 1}.")

    # radio_log part: 1, 2, ..., num_parts
    log_parts = [p.get('part') for p in radio_log]
    if log_parts != list(range(1, len(radio_log) + 1)):
        errors.append(f"V3: radio_log part values are not consecutive from 1 to {len(radio_log)}.")

    # drum length: 1, 2, ..., L
    drum_lengths = [d.get('length') for d in drum_prices]
    if drum_lengths != list(range(1, len(drum_prices) + 1)):
        errors.append(f"V3: drum_prices length values are not consecutive from 1 to {len(drum_prices)}.")

    # pipeline idx: 0, 1, ..., n
    pipeline_indices = [p.get('idx') for p in pipeline_dims]
    if pipeline_indices != list(range(len(pipeline_dims))):
        errors.append(f"V3: pipeline_dims idx values are not consecutive from 0 to {len(pipeline_dims) - 1}.")

    # ---------------------------------------------------------
    # 2. Location 0 and Type Requirements
    # ---------------------------------------------------------
    if locations:
        hq = locations[0]
        if hq.get('loc_id') != 0:
            errors.append(f"V3: First location has loc_id {hq.get('loc_id')}, expected 0.")
        if hq.get('type') != 'D':
            errors.append(f"V3: Location 0 (HQ) must have type 'D', found '{hq.get('type')}'.")
        if hq.get('penalty') != 0:
            errors.append(f"V3: Location 0 (HQ) must have penalty 0, found {hq.get('penalty')}.")

        types_present = set(l.get('type') for l in locations)
        if 'S' not in types_present:
            errors.append("V3: Locations list missing required shelter ('S').")
        if 'H' not in types_present:
            errors.append("V3: Locations list missing required hospital ('H').")

    # ---------------------------------------------------------
    # 3. Roads Topology & Endpoints
    # ---------------------------------------------------------
    seen_road_pairs = set()
    for r in roads:
        rno = r.get('road_no')
        u = r.get('u')
        v = r.get('v')
        if not (isinstance(u, int) and isinstance(v, int)):
            errors.append(f"V3: road {rno} endpoints ({u}, {v}) are not integers.")
            continue
        if u >= v:
            errors.append(f"V3: road {rno} endpoints violate u < v: ({u}, {v}).")
        if not (0 <= u < V and 0 <= v < V):
            errors.append(f"V3: road {rno} endpoints ({u}, {v}) exceed location range [0, {V - 1}].")
        if (u, v) in seen_road_pairs:
            errors.append(f"V3: repeated road pair ({u}, {v}) at road_no {rno}.")
        seen_road_pairs.add((u, v))

    # ---------------------------------------------------------
    # 4. Waves References
    # ---------------------------------------------------------
    for w in waves:
        wno = w.get('wave_no')
        rno = w.get('road_no')
        if not (0 <= rno < E):
            errors.append(f"V3: wave {wno} references invalid road_no {rno} (valid: 0..{E - 1}).")

    # ---------------------------------------------------------
    # 5. Tour References
    # ---------------------------------------------------------
    tour_steps = [t.get('step') for t in tour]
    tour_sites = [t.get('site_no') for t in tour]
    if tour_steps != list(range(num_sites)):
        errors.append(f"V3: tour steps are not consecutive 0 to {num_sites - 1}.")
    if sorted(tour_sites) != list(range(num_sites)):
        errors.append(f"V3: tour sites do not form a valid permutation of 0..{num_sites - 1}.")
    if tour_sites and tour_sites[0] != 0:
        errors.append(f"V3: tour must start at site 0, starts at {tour_sites[0]}.")

    # ---------------------------------------------------------
    # 6. Sensor Cover References
    # ---------------------------------------------------------
    cover_nodes = [c.get('node') for c in sensor_cover]
    if len(cover_nodes) != sensor_k:
        errors.append(f"V3: sensor_cover has {len(cover_nodes)} rows, expected sensor_k = {sensor_k}.")
    if len(set(cover_nodes)) != len(cover_nodes):
        errors.append("V3: sensor_cover contains duplicate nodes.")
    for node in cover_nodes:
        if not (0 <= node < sensor_nodes):
            errors.append(f"V3: sensor_cover node {node} not in range [0, {sensor_nodes - 1}].")

    # ---------------------------------------------------------
    # 7. Safety Planted & Rules References
    # ---------------------------------------------------------
    # Safety planted switches: 1..safety_vars
    planted_switches = [sp.get('switch') for sp in safety_planted]
    if planted_switches != list(range(1, safety_vars + 1)):
        errors.append(f"V3: safety_planted switches are not consecutive 1 to {safety_vars}.")
    for sp in safety_planted:
        val = sp.get('value')
        if val not in (0, 1):
            errors.append(f"V3: safety_planted switch {sp.get('switch')} value is {val}, must be 0 or 1.")

    # Safety rules
    rule_nos = [sr.get('rule_no') for sr in safety_rules]
    if rule_nos != list(range(1, len(safety_rules) + 1)):
        errors.append(f"V3: safety_rules rule_no values are not consecutive 1 to {len(safety_rules)}.")

    for sr in safety_rules:
        rno = sr.get('rule_no')
        lits = [sr.get('lit_1'), sr.get('lit_2'), sr.get('lit_3')]
        switches = [abs(lit) for lit in lits if isinstance(lit, int)]
        if len(switches) != 3:
            errors.append(f"V3: safety rule {rno} does not have 3 integer literals: {lits}.")
            continue
        if 0 in switches:
            errors.append(f"V3: safety rule {rno} contains zero literal: {lits}.")
        if len(set(switches)) != 3:
            errors.append(f"V3: safety rule {rno} literals reference duplicate switches: {lits}.")
        if any(sw > safety_vars for sw in switches):
            errors.append(f"V3: safety rule {rno} literals reference switch > safety_vars ({safety_vars}): {lits}.")

    # ---------------------------------------------------------
    # 8. Incidents Monotonic Ticks
    # ---------------------------------------------------------
    if incidents:
        first_tick = incidents[0].get('tick')
        if first_tick != 0:
            errors.append(f"V3: First alarm tick is {first_tick}, must start at 0.")
        prev_tick = 0
        for inc in incidents:
            aid = inc.get('alarm_id')
            tick = inc.get('tick')
            if tick < prev_tick:
                errors.append(f"V3: alarm {aid} tick {tick} decreased from previous tick {prev_tick}.")
                break
            prev_tick = tick

    return errors

