"""
generate.py - Main Dataset Generator for LIFELINE DAA Project
Generates exactly 50 cases across exactly 20 Excel sheets matching the official specification.

Usage:
    python3 generator/generate.py [--seed <group_seed>] [--output <path_to_cases.xlsx>]
Default seed: 17
Default output: cases.xlsx
"""

import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import argparse
from generator.case_builder import generate_case
from generator.writer import save_workbook

SHEET_SCHEMAS = {
    'cases': [
        'case_id', 'group_seed', 'case_no', 'tier', 'scenario', 'capacity',
        'target_0', 'target_1', 'target_2', 'edit_bound', 'tour_length',
        'sensor_nodes', 'sensor_k', 'safety_vars', 'rations_target'
    ],
    'crates': [
        'case_id', 'crate_id', 'cat', 'weight', 'value', 'expiry', 'serial'
    ],
    'locations': [
        'case_id', 'loc_id', 'type', 'penalty'
    ],
    'roads': [
        'case_id', 'road_no', 'u', 'v', 'minutes', 'cable'
    ],
    'waves': [
        'case_id', 'wave_no', 'road_no'
    ],
    'radio_log': [
        'case_id', 'part', 'text'
    ],
    'radio_patterns': [
        'case_id', 'pattern_no', 'pattern', 'count'
    ],
    'radio_reports': [
        'case_id', 'report_a', 'report_b'
    ],
    'windows': [
        'case_id', 'window_id', 'start', 'finish', 'value'
    ],
    'incidents': [
        'case_id', 'alarm_id', 'tick', 'priority'
    ],
    'sites': [
        'case_id', 'site_no', 'x', 'y'
    ],
    'tour': [
        'case_id', 'step', 'site_no'
    ],
    'pipeline_dims': [
        'case_id', 'idx', 'dim'
    ],
    'drum_prices': [
        'case_id', 'length', 'price'
    ],
    'sensor_edges': [
        'case_id', 'u', 'v'
    ],
    'sensor_cover': [
        'case_id', 'node'
    ],
    'safety_rules': [
        'case_id', 'rule_no', 'lit_1', 'lit_2', 'lit_3'
    ],
    'safety_planted': [
        'case_id', 'switch', 'value'
    ],
    'rations': [
        'case_id', 'item', 'value', 'planted'
    ],
    'claims': [
        'case_id', 'cargo_opt', 'window_count_opt', 'window_value_opt', 'drum_opt', 'tour_opt', 'cover_min'
    ]
}

def build_all_cases(seed=17, num_cases=50):
    """
    Generate all 50 cases and format data rows for all 20 sheets.
    """
    sheets_data = {sheet_name: [cols] for sheet_name, cols in SHEET_SCHEMAS.items()}
    
    print(f"Generating {num_cases} cases with group seed s = {seed}...")
    for case_no in range(num_cases):
        data = generate_case(seed, case_no)
        cid = data['case_id']
        
        # 1. cases
        c = data['cases']
        sheets_data['cases'].append([
            c['case_id'], c['group_seed'], c['case_no'], c['tier'], c['scenario'],
            c['capacity'], c['target_0'], c['target_1'], c['target_2'],
            c['edit_bound'], c['tour_length'], c['sensor_nodes'], c['sensor_k'],
            c['safety_vars'], c['rations_target']
        ])
        
        # 2. crates
        for cr in data['crates']:
            sheets_data['crates'].append([
                cid, cr['crate_id'], cr['cat'], cr['weight'], cr['value'], cr['expiry'], cr['serial']
            ])
            
        # 3. locations
        for loc in data['locations']:
            sheets_data['locations'].append([
                cid, loc['loc_id'], loc['type'], loc['penalty']
            ])
            
        # 4. roads
        for rd in data['roads']:
            sheets_data['roads'].append([
                cid, rd['road_no'], rd['u'], rd['v'], rd['minutes'], rd['cable']
            ])
            
        # 5. waves
        for wv in data['waves']:
            sheets_data['waves'].append([
                cid, wv['wave_no'], wv['road_no']
            ])
            
        # 6. radio_log
        for rl in data['radio_log']:
            sheets_data['radio_log'].append([
                cid, rl['part'], rl['text']
            ])
            
        # 7. radio_patterns
        for rp in data['radio_patterns']:
            sheets_data['radio_patterns'].append([
                cid, rp['pattern_no'], rp['pattern'], rp['count']
            ])
            
        # 8. radio_reports
        for rep in data['radio_reports']:
            sheets_data['radio_reports'].append([
                cid, rep['report_a'], rep['report_b']
            ])
            
        # 9. windows
        for w in data['windows']:
            sheets_data['windows'].append([
                cid, w['window_id'], w['start'], w['finish'], w['value']
            ])
            
        # 10. incidents
        for inc in data['incidents']:
            sheets_data['incidents'].append([
                cid, inc['alarm_id'], inc['tick'], inc['priority']
            ])
            
        # 11. sites
        for st in data['sites']:
            sheets_data['sites'].append([
                cid, st['site_no'], st['x'], st['y']
            ])
            
        # 12. tour
        for tr in data['tour']:
            sheets_data['tour'].append([
                cid, tr['step'], tr['site_no']
            ])
            
        # 13. pipeline_dims
        for pd in data['pipeline_dims']:
            sheets_data['pipeline_dims'].append([
                cid, pd['idx'], pd['dim']
            ])
            
        # 14. drum_prices
        for dp in data['drum_prices']:
            sheets_data['drum_prices'].append([
                cid, dp['length'], dp['price']
            ])
            
        # 15. sensor_edges
        for se in data['sensor_edges']:
            sheets_data['sensor_edges'].append([
                cid, se['u'], se['v']
            ])
            
        # 16. sensor_cover
        for sc in data['sensor_cover']:
            sheets_data['sensor_cover'].append([
                cid, sc['node']
            ])
            
        # 17. safety_rules
        for sr in data['safety_rules']:
            sheets_data['safety_rules'].append([
                cid, sr['rule_no'], sr['lit_1'], sr['lit_2'], sr['lit_3']
            ])
            
        # 18. safety_planted
        for sp in data['safety_planted']:
            sheets_data['safety_planted'].append([
                cid, sp['switch'], sp['value']
            ])
            
        # 19. rations
        for rt in data['rations']:
            sheets_data['rations'].append([
                cid, rt['item'], rt['value'], rt['planted']
            ])
            
        # 20. claims (Tier S only)
        if data['claims'] is not None:
            cl = data['claims']
            sheets_data['claims'].append([
                cl['case_id'], cl['cargo_opt'], cl['window_count_opt'],
                cl['window_value_opt'], cl['drum_opt'], cl['tour_opt'], cl['cover_min']
            ])

    return sheets_data

def main():
    parser = argparse.ArgumentParser(description="LIFELINE Cases Generator")
    parser.add_argument("--seed", type=int, default=17, help="Group seed (default: 17)")
    parser.add_argument("--output", type=str, default="cases.xlsx", help="Output path (default: cases.xlsx)")
    args = parser.parse_args()

    sheets = build_all_cases(seed=args.seed, num_cases=50)
    output_path = os.path.abspath(args.output)
    print(f"Writing workbook to {output_path}...")
    save_workbook(sheets, output_path)
    print(f"Successfully generated {output_path} ({len(sheets)} sheets).")

if __name__ == "__main__":
    main()
