"""
v4_graph.py - Network connectivity and closure waves validation for LIFELINE Phase 1 Validator.

Verifies:
1. Network connectivity before any closures:
   - Entire road network must form a single connected component reachable from HQ (node 0)
     using independent Breadth-First Search (BFS).
2. Closure waves disjointness:
   - No road may appear in more than one wave.
3. Waves count:
   - Exactly 2 to 5 closure waves.
4. Wave indexing:
   - Wave numbers must be consecutive with no gaps.
   - Note on SPEC CONFLICT: The prompt notes mention 'wave_no consecutive from 1', but the
     PDF Section 3 (page 4) does not prescribe 1-based indexing for waves, and generator
     datasets use 0-indexed wave numbers (0..num_waves-1). Under Rule 2, consecutive from
     either 0 or 1 is accepted.
5. Road count per wave:
   - Each wave must contain between 1 and max(1, floor(E / 4)) roads.
"""

import math
from algos import is_graph_connected


def validate_case_v4(case_id, case_data):
    """
    Validates graph connectivity and closure wave rules for a single case.
    
    Args:
        case_id (str): Identifier, e.g., '18-00'.
        case_data (dict): Mapping of sheet_name -> list of row dicts.
        
    Returns:
        list of str: List of detected V4 errors.
    """
    errors = []

    locations = case_data.get('locations', [])
    roads = case_data.get('roads', [])
    waves = case_data.get('waves', [])

    V = len(locations)
    E = len(roads)

    if V == 0 or E == 0:
        return errors  # Handled in V1/V2

    # -------------------------------------------------------------
    # 1. Connected before closures (BFS from HQ = 0)
    # -------------------------------------------------------------
    edge_pairs = [(r['u'], r['v']) for r in roads]
    connected, reachable = is_graph_connected(V, edge_pairs, start_node=0)
    if not connected:
        errors.append(
            f"V4: Graph is disconnected before closures; only {len(reachable)} "
            f"of {V} locations are reachable from HQ (0)."
        )

    # -------------------------------------------------------------
    # 2. Waves Disjointness and Size Limits
    # -------------------------------------------------------------
    if not waves:
        errors.append("V4: Missing rows in 'waves' sheet.")
        return errors

    # Check for duplicate roads across waves (disjoint waves)
    seen_roads = set()
    duplicate_roads = set()
    waves_by_no = {}

    for w in waves:
        wno = w.get('wave_no')
        rno = w.get('road_no')

        if rno in seen_roads:
            duplicate_roads.add(rno)
        seen_roads.add(rno)

        if wno not in waves_by_no:
            waves_by_no[wno] = []
        waves_by_no[wno].append(rno)

    if duplicate_roads:
        errors.append(f"V4: Waves are not disjoint; roads appear in multiple waves: {sorted(list(duplicate_roads))}.")

    # 3. Wave count between 2 and 5
    num_waves = len(waves_by_no)
    if not (2 <= num_waves <= 5):
        errors.append(f"V4: distinct wave count {num_waves} not in range [2, 5].")

    # 4. Wave numbers consecutive with no gaps (0-based or 1-based)
    sorted_wave_nos = sorted(waves_by_no.keys())
    expected_0 = list(range(num_waves))
    expected_1 = list(range(1, num_waves + 1))
    if sorted_wave_nos != expected_0 and sorted_wave_nos != expected_1:
        errors.append(f"V4: wave_no values {sorted_wave_nos} are not consecutive (expected {expected_0} or {expected_1}).")

    # 5. Roads per wave limit: 1 to max(1, floor(E / 4))
    max_roads_per_wave = max(1, math.floor(E / 4))
    for wno, wave_roads in sorted(waves_by_no.items()):
        cnt = len(wave_roads)
        if cnt < 1 or cnt > max_roads_per_wave:
            errors.append(
                f"V4: wave {wno} contains {cnt} roads, expected between 1 and {max_roads_per_wave} (floor({E}/4))."
            )

    return errors

