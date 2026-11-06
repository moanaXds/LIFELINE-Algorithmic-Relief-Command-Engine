"""
v2_ranges.py - Tier sizes and field range validation for LIFELINE Phase 1 Validator.

Verifies:
1. Sizing constraints per tier (S, M, L, and hostile traps X):
   - Crates count
   - Locations count (V)
   - Roads count (E in V-1..3V)
   - Waves count (2..5)
   - Total radio log symbols
   - Radio report lengths (report_a, report_b)
   - Time windows count
   - Alarms count
   - Relief sites count
   - Pipeline stages n (idx runs 0..n)
   - Drum length L (length runs 1..L)
   - Sensor nodes (sensor_nodes in cases)
   - Safety variables (safety_vars in cases)
   - Ration items count
2. Field value ranges:
   - capacity (10% to 70% of total crate weight, and >= 1)
   - crate cat (0..4), weight (1..20), value (10..100), expiry (0..999), serial (8-digit, distinct)
   - location penalty in {0, 1, 2, 4, 6}, type in {'D', 'S', 'H', 'J'}
   - road minutes (1..60), cable (1..100)
   - window start/finish (0 <= start < finish <= 1440), duration (5..480), value (1..100)
   - alarm priority (1..10)
   - site coordinates x, y (0..999)
   - pipeline dimension (2..100)
   - drum price (1..500)
   - ration item value (1..1000)
   - targets: 3 distinct S/H locations, never HQ (location 0)
"""

# Size ranges by tier (min, max inclusive)
TIER_SIZE_RANGES = {
    'crates': {
        'S': (8, 20),
        'M': (40, 200),
        'L': (500, 1500),
        'X': (500, 1500)  # Default for X; traps 46/47 override below
    },
    'locations': {
        'S': (6, 12),
        'M': (30, 150),
        'L': (500, 2000),
        'X': (500, 2000)  # Default for X; trap 48 overrides below
    },
    'log_symbols': {
        'S': (200, 500),
        'M': (2000, 10000),
        'L': (20000, 100000),
        'X': (20000, 100000)  # Default for X; trap 49 overrides below
    },
    'report_len': {
        'S': (10, 30),
        'M': (30, 150),
        'L': (200, 1000),
        'X': (200, 1000)
    },
    'windows': {
        'S': (8, 20),
        'M': (50, 300),
        'L': (1000, 3000),
        'X': (1000, 3000)
    },
    'alarms': {
        'S': (10, 40),
        'M': (200, 1000),
        'L': (2000, 5000),
        'X': (2000, 5000)
    },
    'sites': {
        'S': (5, 9),
        'M': (10, 16),
        'L': (200, 500),
        'X': (200, 500)
    },
    'pipeline_stages': {
        'S': (4, 8),
        'M': (15, 60),
        'L': (100, 300),
        'X': (100, 300)
    },
    'drum_length': {
        'S': (5, 14),
        'M': (40, 200),
        'L': (500, 2000),
        'X': (500, 2000)
    },
    'sensor_nodes': {
        'S': (6, 14),
        'M': (20, 40),
        'L': (100, 400),
        'X': (100, 400)
    },
    'safety_vars': {
        'S': (6, 15),
        'M': (20, 50),
        'L': (20, 50),
        'X': (20, 50)
    },
    'ration_items': {
        'S': (8, 20),
        'M': (24, 40),
        'L': (50, 100),
        'X': (50, 100)
    }
}


def get_expected_size_range(item, tier, case_no):
    """
    Returns the (min, max) allowable range for a given item, tier, and case number.
    Handles specific overrides for hostile trap cases (46-49).
    """
    # Hostile trap specific ranges
    if case_no == 46 and item == 'crates':
        return (1500, 3000)
    if case_no == 47 and item == 'crates':
        return (12, 60)
    if case_no == 48 and item == 'locations':
        return (1500, 3000)
    if case_no == 49 and item == 'log_symbols':
        return (50000, 100000)

    return TIER_SIZE_RANGES[item][tier]


def validate_case_v2(case_id, case_data):
    """
    Validates tier sizes and field ranges for a single case.
    
    Args:
        case_id (str): Identifier, e.g., '18-00'.
        case_data (dict): Mapping of sheet_name -> list of row dicts.
        
    Returns:
        list of str: List of detected V2 errors.
    """
    errors = []
    
    cases_rows = case_data.get('cases', [])
    if not cases_rows:
        return errors  # Handled in V1
    case_meta = cases_rows[0]
    case_no = case_meta.get('case_no', 0)
    tier = case_meta.get('tier', 'S')

    crates = case_data.get('crates', [])
    locations = case_data.get('locations', [])
    roads = case_data.get('roads', [])
    waves = case_data.get('waves', [])
    radio_log = case_data.get('radio_log', [])
    radio_reports = case_data.get('radio_reports', [])
    windows = case_data.get('windows', [])
    incidents = case_data.get('incidents', [])
    sites = case_data.get('sites', [])
    pipeline_dims = case_data.get('pipeline_dims', [])
    drum_prices = case_data.get('drum_prices', [])
    rations = case_data.get('rations', [])

    # ---------------------------------------------------------
    # 1. Tier Size Checks
    # ---------------------------------------------------------
    
    # Crates count
    low, high = get_expected_size_range('crates', tier, case_no)
    if not (low <= len(crates) <= high):
        errors.append(f"V2: crates count {len(crates)} not in range [{low}, {high}] for tier {tier}.")

    # Locations count (V)
    V = len(locations)
    low, high = get_expected_size_range('locations', tier, case_no)
    if not (low <= V <= high):
        errors.append(f"V2: locations count {V} not in range [{low}, {high}] for tier {tier}.")

    # Roads count (E): V - 1 <= E <= 3 * V
    E = len(roads)
    if V > 0 and not (V - 1 <= E <= 3 * V):
        errors.append(f"V2: roads count {E} not in range [V-1, 3V] = [{V-1}, {3*V}].")

    # Waves count: 2 to 5 closure waves across all tiers
    distinct_waves = set(w.get('wave_no') for w in waves if w.get('wave_no') is not None)
    if not (2 <= len(distinct_waves) <= 5):
        errors.append(f"V2: distinct waves count {len(distinct_waves)} not in range [2, 5].")

    # Radio log symbols total length
    total_log_len = sum(len(p.get('text', '')) for p in radio_log)
    low, high = get_expected_size_range('log_symbols', tier, case_no)
    if not (low <= total_log_len <= high):
        errors.append(f"V2: total radio log length {total_log_len} not in range [{low}, {high}] for tier {tier}.")

    # Radio report lengths
    if radio_reports:
        rep_a = radio_reports[0].get('report_a', '')
        rep_b = radio_reports[0].get('report_b', '')
        low, high = get_expected_size_range('report_len', tier, case_no)
        if not (low <= len(rep_a) <= high):
            errors.append(f"V2: report_a length {len(rep_a)} not in range [{low}, {high}] for tier {tier}.")
        if not (low <= len(rep_b) <= high):
            errors.append(f"V2: report_b length {len(rep_b)} not in range [{low}, {high}] for tier {tier}.")

    # Windows count
    low, high = get_expected_size_range('windows', tier, case_no)
    if not (low <= len(windows) <= high):
        errors.append(f"V2: windows count {len(windows)} not in range [{low}, {high}] for tier {tier}.")

    # Alarms count
    low, high = get_expected_size_range('alarms', tier, case_no)
    if not (low <= len(incidents) <= high):
        errors.append(f"V2: alarms count {len(incidents)} not in range [{low}, {high}] for tier {tier}.")

    # Relief sites count
    low, high = get_expected_size_range('sites', tier, case_no)
    if not (low <= len(sites) <= high):
        errors.append(f"V2: relief sites count {len(sites)} not in range [{low}, {high}] for tier {tier}.")

    # Pipeline stages n (idx 0..n => n + 1 entries => stages = len - 1)
    pipeline_n = len(pipeline_dims) - 1 if pipeline_dims else 0
    low, high = get_expected_size_range('pipeline_stages', tier, case_no)
    if not (low <= pipeline_n <= high):
        errors.append(f"V2: pipeline stages {pipeline_n} not in range [{low}, {high}] for tier {tier}.")

    # Drum length L (length runs 1..L => len(drum_prices) entries)
    drum_L = len(drum_prices)
    low, high = get_expected_size_range('drum_length', tier, case_no)
    if not (low <= drum_L <= high):
        errors.append(f"V2: drum length {drum_L} not in range [{low}, {high}] for tier {tier}.")

    # Sensor nodes (from cases sheet column sensor_nodes)
    sensor_nodes = case_meta.get('sensor_nodes', 0)
    low, high = get_expected_size_range('sensor_nodes', tier, case_no)
    if not (low <= sensor_nodes <= high):
        errors.append(f"V2: sensor_nodes {sensor_nodes} not in range [{low}, {high}] for tier {tier}.")

    # Safety variables (from cases sheet column safety_vars)
    safety_vars = case_meta.get('safety_vars', 0)
    low, high = get_expected_size_range('safety_vars', tier, case_no)
    if not (low <= safety_vars <= high):
        errors.append(f"V2: safety_vars {safety_vars} not in range [{low}, {high}] for tier {tier}.")

    # Ration items count
    low, high = get_expected_size_range('ration_items', tier, case_no)
    if not (low <= len(rations) <= high):
        errors.append(f"V2: ration items count {len(rations)} not in range [{low}, {high}] for tier {tier}.")

    # ---------------------------------------------------------
    # 2. Field Value Ranges
    # ---------------------------------------------------------
    
    # Capacity: 10% to 70% of total crate weight, and >= 1
    total_crate_weight = sum(c.get('weight', 0) for c in crates)
    capacity = case_meta.get('capacity', 0)
    if total_crate_weight > 0:
        pct = capacity / total_crate_weight
        if capacity < 1 or pct < 0.10 or pct > 0.70:
            errors.append(
                f"V2: capacity {capacity} is {pct*100:.2f}% of total crate weight {total_crate_weight} "
                f"(required: 10% to 70% and >= 1)."
            )

    # Crates fields: cat 0-4; weight 1-20; value 10-100; expiry 0-999; serial 8-digit distinct
    serials_seen = set()
    for c in crates:
        crid = c.get('crate_id')
        cat = c.get('cat')
        wt = c.get('weight')
        val = c.get('value')
        exp = c.get('expiry')
        ser = c.get('serial')

        if cat not in (0, 1, 2, 3, 4):
            errors.append(f"V2: crate {crid} cat {cat} not in [0, 4].")
        if not (1 <= wt <= 20):
            errors.append(f"V2: crate {crid} weight {wt} not in [1, 20].")
        if not (10 <= val <= 100):
            errors.append(f"V2: crate {crid} value {val} not in [10, 100].")
        if not (0 <= exp <= 999):
            errors.append(f"V2: crate {crid} expiry {exp} not in [0, 999].")
        if not (10000000 <= ser <= 99999999):
            errors.append(f"V2: crate {crid} serial {ser} not an 8-digit integer [10000000, 99999999].")
        if ser in serials_seen:
            errors.append(f"V2: crate {crid} duplicate serial {ser} in case.")
        serials_seen.add(ser)

    # Locations fields: penalty in {0, 1, 2, 4, 6}, type in {'D', 'S', 'H', 'J'}
    loc_by_id = {}
    for loc in locations:
        lid = loc.get('loc_id')
        ltype = loc.get('type')
        pen = loc.get('penalty')
        loc_by_id[lid] = loc

        if ltype not in ('D', 'S', 'H', 'J'):
            errors.append(f"V2: location {lid} type '{ltype}' not in ['D', 'S', 'H', 'J'].")
        if pen not in (0, 1, 2, 4, 6):
            errors.append(f"V2: location {lid} penalty {pen} not in {{0, 1, 2, 4, 6}}.")

    # Targets: 3 distinct S/H locations, never HQ (location 0)
    t0 = case_meta.get('target_0')
    t1 = case_meta.get('target_1')
    t2 = case_meta.get('target_2')
    targets = [t0, t1, t2]

    if len(set(targets)) != 3:
        errors.append(f"V2: targets {targets} are not 3 distinct locations.")
    if 0 in targets:
        errors.append(f"V2: targets {targets} must not include HQ (location 0).")
    for t in targets:
        if t not in loc_by_id:
            errors.append(f"V2: target {t} is not a valid location ID.")
        else:
            t_type = loc_by_id[t].get('type')
            if t_type not in ('S', 'H'):
                errors.append(f"V2: target {t} has type '{t_type}', expected 'S' or 'H'.")

    # Roads fields: minutes 1-60, cable 1-100
    for r in roads:
        rno = r.get('road_no')
        m = r.get('minutes')
        c = r.get('cable')
        if not (1 <= m <= 60):
            errors.append(f"V2: road {rno} minutes {m} not in [1, 60].")
        if not (1 <= c <= 100):
            errors.append(f"V2: road {rno} cable {c} not in [1, 100].")

    # Windows fields: 0 <= start < finish <= 1440, duration 5-480, value 1-100
    for w in windows:
        wid = w.get('window_id')
        s = w.get('start')
        f = w.get('finish')
        val = w.get('value')
        if not (0 <= s < f <= 1440):
            errors.append(f"V2: window {wid} interval [{s}, {f}] violates 0 <= start < finish <= 1440.")
        dur = f - s
        if not (5 <= dur <= 480):
            errors.append(f"V2: window {wid} duration {dur} not in [5, 480].")
        if not (1 <= val <= 100):
            errors.append(f"V2: window {wid} value {val} not in [1, 100].")

    # Alarms fields: priority 1-10
    for inc in incidents:
        aid = inc.get('alarm_id')
        prio = inc.get('priority')
        if not (1 <= prio <= 10):
            errors.append(f"V2: alarm {aid} priority {prio} not in [1, 10].")

    # Sites fields: x, y in 0-999
    for s in sites:
        sno = s.get('site_no')
        x = s.get('x')
        y = s.get('y')
        if not (0 <= x <= 999 and 0 <= y <= 999):
            errors.append(f"V2: site {sno} coordinates ({x}, {y}) not in [0, 999].")

    # Pipeline dims fields: dim in 2-100
    for p in pipeline_dims:
        idx = p.get('idx')
        dim = p.get('dim')
        if not (2 <= dim <= 100):
            errors.append(f"V2: pipeline idx {idx} dim {dim} not in [2, 100].")

    # Drum prices fields: price in 1-500
    for d in drum_prices:
        lng = d.get('length')
        pr = d.get('price')
        if not (1 <= pr <= 500):
            errors.append(f"V2: drum length {lng} price {pr} not in [1, 500].")

    # Ration values: 1-1000
    for rat in rations:
        item = rat.get('item')
        val = rat.get('value')
        if not (1 <= val <= 1000):
            errors.append(f"V2: ration item {item} value {val} not in [1, 1000].")

    # Sensor cover size k: 2 <= k <= n / 2
    sensor_k = case_meta.get('sensor_k', 0)
    if not (2 <= sensor_k <= sensor_nodes // 2):
        errors.append(f"V2: sensor_k {sensor_k} not in [2, floor({sensor_nodes}/2)].")

    return errors

