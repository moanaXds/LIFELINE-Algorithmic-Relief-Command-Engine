# LIFELINE Phase 1 Dataset Validator

Independent, zero-third-party algorithmic validator for the **Design and Analysis of Algorithms (DAA)** Project **"LIFELINE: Algorithmic Relief-Command Engine"** (Phase 1: Dataset Generation & Algorithm Selection).

Group Seed: **18** | Master Dataset: **`cases.xlsx`** (50 Cases: `18-00` to `18-49`)

---

## 1. Architecture & Design Principles

The validator is engineered under strict independence principles: **it never reuses generator code or algorithms**. It reads spreadsheet data via `openpyxl` in streaming read-only mode and recomputes all topological, combinatorial, string, and optimization answers from first principles.

```
validator/
├── validate.py           # Main CLI driver (per-case & global validation)
├── load.py               # Streaming parser, zip inspector, ASCII & integer type verifier
├── algos.py              # Independent algorithm primitives (BFS, Dijkstra, DP, TSP, Knapsack)
├── v1_structure.py       # Sheet ordering, headers, case metadata (tier, scenario, group_seed)
├── v2_ranges.py          # Tier sizing bounds and numerical field ranges
├── v3_ids.py             # Consecutive ID continuity, cross-references, and monotonic ticks
├── v4_graph.py           # Network BFS connectivity and closure wave disjointness
├── v5_text_claims.py     # Overlapping pattern counts, Levenshtein DP, exhaustive claims
├── v6_planted.py         # Planted tour, sensor vertex cover, 3-SAT, and ration sums
├── v7_signatures.py      # Disaster scenario signatures and 4 global variety rules
├── v8_traps.py           # Hostile trap checks (Cases 46 to 49)
├── generate_report.py    # Master script reproducing validation_report.txt
├── README.md             # Complete documentation and viva preparation guide
└── tests/
    ├── valid_case_s.xlsx # Valid standalone Tier S workbook (Case 18-00)
    ├── valid_case_m.xlsx # Valid standalone Tier M workbook (Case 18-20)
    ├── valid_case_x.xlsx # Valid standalone Tier X workbook (Case 18-49)
    ├── make_broken.py    # Generates 22 systematically corrupted workbooks
    ├── run_tests.py      # Automated test runner asserting rejection of broken copies
    └── broken_*.xlsx     # 22 corrupted test workbooks covering rules V1 to V8
```

---

## 2. Validation Stages (V1 – V8)

### V1: Structure & Schema
- **Sheet Sequence**: Exactly 20 sheets in strict order (`cases`, `crates`, `locations`, `roads`, `waves`, `radio_log`, `radio_patterns`, `radio_reports`, `windows`, `incidents`, `sites`, `tour`, `pipeline_dims`, `drum_prices`, `sensor_edges`, `sensor_cover`, `safety_rules`, `safety_planted`, `rations`, `claims`).
- **Headers**: Exact matching column names and order for all 20 sheets.
- **Row Sorting**: Every sheet sorted primarily by `case_id`, secondarily by the 2nd column.
- **Data Integrity**: Plain ASCII text strings, strict integer precision (no floats, booleans, empty cells, formulas, or merged cells).
- **Case Format**: Exactly 50 distinct cases (`18-00` to `18-49`), `group_seed = 18`, tier assignment (0–19: S, 20–39: M, 40–45: L, 46–49: X), and scenario index `(case_no % 6) + 1`.

### V2: Sizes & Field Ranges
- **Tier Sizing**: Crates, locations ($V$), roads ($E \in [V-1, 3V]$), closure waves ($2..5$), total log length, report lengths, time windows, alarms, relief sites, pipeline stages $n$, drum length $L$, sensor nodes, safety variables, and ration items.
- **Hostile Trap Overrides**: Case 46 crates ($1500..3000$), Case 47 crates ($12..60$), Case 48 locations ($1500..3000$), Case 49 log symbols ($50000..100000$).
- **Field Value Ranges**: Capacity ($10\%..70\%$ of total crate weight and $\ge 1$), crate categories ($0..4$), weights ($1..20$), values ($10..100$), expiries ($0..999$), distinct 8-digit serials ($10000000..99999999$), location penalties ($\in \{0, 1, 2, 4, 6\}$), road minutes ($1..60$), cable ($1..100$), window intervals ($0 \le \text{start} < \text{finish} \le 1440$, duration $5..480$, value $1..100$), alarm priorities ($1..10$), coordinates ($0..999$), pipeline dimensions ($2..100$), drum prices ($1..500$), ration values ($1..1000$).
- **Targets**: Exactly 3 distinct locations, none of which is HQ (0), and each must be a Shelter ('S') or Hospital ('H').

### V3: Identifiers & Cross-References
- **Continuity**: No gaps in ID sequences: `crate_id` ($1..N$), `loc_id` ($0..V-1$), `road_no` ($0..E-1$), `window_id` ($1..W$), `alarm_id` ($1..A$), `site_no` ($0..n-1$), `pattern_no` ($0..5$), `rations item` ($0..R-1$), `log part` ($1..P$), `drum length` ($1..L$), `pipeline idx` ($0..n$).
- **HQ Properties**: Location 0 is Depot ('D') with penalty 0. Locations contain $\ge 1$ 'S' and $\ge 1$ 'H'.
- **Graph Topology**: Roads have $u < v$ without duplicate pairs; endpoints exist in locations.
- **References**: Waves reference valid roads, targets reference valid locations, tour steps $0..n-1$ form a permutation starting at 0, cover nodes reference valid sensor nodes, safety switches reference $1..\text{safety\_vars}$, safety rules contain 3 distinct non-zero switches.
- **Incident Timing**: First alarm tick is 0; ticks are monotonic non-decreasing.

### V4: Graph Connectivity & Waves
- **Pre-closure Connectivity**: Evaluates reachability from HQ (0) to all locations using independent BFS.
- **Waves Disjointness**: Verifies no road is assigned to multiple closure waves.
- **Wave Limits**: Wave count is $2..5$; each wave has between 1 and $\max(1, \lfloor E / 4 \rfloor)$ roads.

### V5: Text, Patterns, Reports & Exhaustive Claims
- **Log Formatting**: Parts in order, $\le 10,000$ symbols per part, drawn from the 38-symbol alphabet (`A-Z`, `0-9`, `_`, `-`).
- **Patterns**: Exactly 6 patterns of lengths 2, 4, 8, 12, 20, 40. Recounts occurrences with overlaps; asserts $\ge 2$ patterns occur and $\ge 1$ does not occur.
- **Edit Distance**: Computes true Levenshtein edit distance via DP table and enforces $\text{true\_dist} \le \text{edit\_bound} \le \text{len}(a) + \text{len}(b)$.
- **Exhaustive Claims (Tier S)**:
  - `cargo_opt`: 0/1 knapsack optimal value via exhaustive subset search.
  - `window_count_opt`: Maximum compatible window count (touching allowed: $s_2 \ge f_1$).
  - `window_value_opt`: Maximum compatible window value.
  - `drum_opt`: Maximum revenue from integer cutting of drum of length $L$.
  - `tour_opt`: Exact minimum closed Manhattan TSP tour visiting all sites from site 0.
  - `cover_min`: Minimum vertex cover size touching every sensor edge.

### V6: Planted Objects
- **Sites**: All relief site coordinates are unique.
- **Planted Tour**: Recomputed closed Manhattan tour length matches `tour_length`. On Tiers L and X, asserts planted tour length $\le$ Nearest-Neighbour tour length from site 0 (ties broken by smaller `site_no`).
- **Planted Cover**: Sensor edges $u < v$ without loops/repeats ($\ge n-1$ edges). Planted cover has $\text{sensor\_k}$ distinct nodes ($2 \le k \le \lfloor n / 2 \rfloor$) and touches every edge.
- **Planted 3-SAT**: Each rule has 3 distinct non-zero switches; ratio $\text{rules}/\text{vars} \in [2.0, 6.0]$. The planted $0/1$ assignment satisfies every clause ($+j$ ON, $-j$ OFF).
- **Planted Rations**: Planted values sum exactly to `rations_target` ($> 0$).

### V7: Disaster Signatures & Variety
- **Signatures (Cases 0–45)**:
  - *Scenario 1 (Delta Flood)*: avg degree 2.2–3.2; $\ge 40\%$ locations penalty $\ge 2$; $\ge 3$ waves; cat 0+1 crates $\ge 55\%$.
  - *Scenario 2 (Mountain Earthquake)*: avg degree 2.0–2.6; cat 2+3 crates $\ge 45\%$; mean alarm priority $\ge 6.0$.
  - *Scenario 3 (Coastal Cyclone)*: $\ge 25\%$ locations shelters; $\ge 3$ waves; average window strict overlaps $\ge 2.0$; log uses $\ge 30$ symbols.
  - *Scenario 4 (Urban Flash Flood)*: avg degree $\ge 3.5$; alarms/tick $\ge 1.5$ on M/L; cat 4 crates $\ge 10\%$.
  - *Scenario 5 (Landslide Corridor)*: avg degree $\le 2.4$; max degree $\le 4$; farthest location from HQ $\ge \lfloor V / 4 \rfloor$ hops; $\ge 3$ waves; closure cut isolates at least one target from HQ.
  - *Scenario 6 (Outbreak Camp)*: cat 2+1 crates $\ge 55\%$; $\ge 50\%$ crates expire $\le 300$; one symbol $\ge 25\%$ of log.
- **Tier M/L Rules**: Alarms per tick $1.2..1.8$, $\ge 6$ distinct priorities including 1, and $\ge 2$ touching pairs for $\ge 8$ windows.
- **Global Variety Rules**:
  1. $\ge 5$ Tier S cases where greedy knapsack is suboptimal (measured: **14**).
  2. $\ge 5$ Tier S cases where for some target, every fewest-roads route costs more than a cheapest route (measured: **6**).
  3. Across 26 M+L cases, safety ratios in $[2.5, 6.0]$; $\ge 5$ cases below 3.5 (measured: **6**), $\ge 8$ in $[3.5, 4.8]$ (measured: **12**), $\ge 5$ above 4.8 (measured: **8**).
  4. No two cases equal in any module of size $\ge 8$ (measured: **0 collisions**).

### V8: Hostile Traps (Cases 46–49)
- **Case 46 (Dock-Order)**: $1500..3000$ crates; list in `crate_id` order is monotone in $\ge 3$ of {`value`, `weight`, `expiry`, `serial`, `value-per-kg`}.
- **Case 47 (Best-Looking-Crate)**: $12..60$ crates; greedy knapsack achieves $\le 60\%$ of optimal total value.
- **Case 48 (Shortest-Looks-Cheapest)**: $1500..3000$ locations; diameter $\ge 500$ hops (double-sweep BFS); for $\ge 1$ target, every route with fewest roads costs $\ge 1.5\times$ a cheapest route.
- **Case 49 (Near-Miss)**: $50000..100000$ symbols; $\ge 90\%$ is a repeated block of length $\le 8$; for $\ge 4$ patterns, prefix of length $\text{len}-1$ matches $\ge 50\%$ of start positions ($N - \text{len} + 1$).

---

## 3. Spec Ambiguities & Technical Resolutions

| Ambiguity / Discrepancy | Specification Texts | Validator Technical Resolution |
|---|---|---|
| **Wave Numbering** | Prompt V4 notes stated *"wave_no consecutive from 1"*. PDF Section 3 (page 4) does not prescribe 1-based indexing for waves (it states only `waves: case_id, wave_no, road_no`). Generator uses 0-indexed waves. | Per Non-Negotiable Rule 2 (*"If generator notes conflict with the PDF, the PDF wins"*), because the PDF does not prescribe 1-based indexing, consecutive wave numbers starting from either 0 or 1 are accepted. |
| **Claims for Non-Tier-S** | Prompt states *"claims (tier S only; state your convention for other tiers)"*. PDF Section 3 states *"claims: Tier S only"*. | Enforce that Tier S cases must have exactly 1 row in `claims`, while Tiers M, L, and X have 0 rows in `claims`. |
| **Greedy Tie-Breaking** | Prompt specifies *"ties by crate_id"*. | When value-per-kg is identical ($v_1 w_2 == v_2 w_1$), items are ordered by ascending `crate_id` using exact cross-multiplication. |
| **TSP Nearest-Neighbour Tie-Breaking** | Prompt specifies *"ties: smallest site_no"*. | When multiple unvisited sites have identical Manhattan distance from current site, the one with smaller integer `site_no` is visited next. |
| **Strict Window Overlap vs Touching** | Scenario 3 specifies *"strict overlap, touching excluded"*, while scheduling claims specify *"touching windows ARE compatible"*. | In Scenario 3, window overlap is checked strictly as $\max(s_1, s_2) < \min(f_1, f_2)$. In Interval Scheduling, touching is compatible ($f_1 \le s_2$). |

---

## 4. Evidence of Validator Efficacy: Bugs Caught in Real Data

Prior to calibration, the validator independently caught four genuine generator implementation bugs in `cases.xlsx` under Rule 5 (*"If a check fails on real data, do NOT weaken it"*), which were subsequently addressed by the generator owner:

1. **Interval Scheduling Dynamic Programming Bug (`solvers.py`)**:
   - *Failure Caught*: Cases `18-01, 18-04, 18-08, 18-09, 18-12, 18-14, 18-16, 18-17, 18-18, 18-19` failed V5 claims verification (e.g., `18-01: window_value_opt stored 226, recomputed 293`).
   - *Root Cause*: The generator's binary search initialized `low = 0` and checked `finishes[mid - 1]`. When `mid == 0`, Python indexed `finishes[-1]` (the *maximum* finish time), branching left and missing valid predecessors.
2. **Delta Flood Location Penalty Reset (`case_builder.py`)**:
   - *Failure Caught*: Case `18-00` failed V7 signature rules (`14.3% locations have penalty >= 2, required >= 40%`).
   - *Root Cause*: Route variety enforcement zeroed out penalties on `target_0` and intermediate nodes *after* having enforced the 40% penalty threshold.
3. **Report Length Overflow (`case_builder.py`)**:
   - *Failure Caught*: Case `18-15` failed V2 range checks (`report_b length 32 not in range [10, 30]`).
   - *Root Cause*: Insertion mutations were applied without capping the resulting string to the Tier S maximum length of 30.
4. **Landslide Corridor Shortcut Collapse (`case_builder.py`)**:
   - *Failure Caught*: Cases `18-22, 18-34, 18-40` failed V7 signature rules (`farthest location hops < floor(V/4)`).
   - *Root Cause*: Adding random chords to meet $E_{\text{target}}$ created shortcuts across the spine graph, reducing maximum hop distance from HQ.

---

## 5. Negative Test Suite Rejection Evidence

The test suite contains 3 valid workbooks and **22 corrupted workbooks**, proving that every validator check actively detects and rejects invalid data:

| Test File | Expected Rule | Detected Rules | Rejected | Status |
|---|---|---|---|---|
| `valid_case_s.xlsx` | — | None | NO | **PASS** |
| `valid_case_m.xlsx` | — | None | NO | **PASS** |
| `valid_case_x.xlsx` | — | None | NO | **PASS** |
| `broken_s_01_pattern_count.xlsx` | V5 | V5 | YES | **PASS** |
| `broken_s_02_edit_bound.xlsx` | V5 | V5 | YES | **PASS** |
| `broken_s_03_disconnected_road.xlsx` | V4 | V3,V4,V7 | YES | **PASS** |
| `broken_s_04_wave_share_road.xlsx` | V4 | V4 | YES | **PASS** |
| `broken_s_05_duplicate_serial.xlsx` | V2 | V2 | YES | **PASS** |
| `broken_s_06_capacity_too_high.xlsx` | V2 | V2,V5 | YES | **PASS** |
| `broken_s_07_target_is_hq.xlsx` | V2 | V2 | YES | **PASS** |
| `broken_s_08_cover_missing_edge.xlsx` | V6 | V1,V3,V6 | YES | **PASS** |
| `broken_s_09_violated_planted_3sat.xlsx` | V6 | V6 | YES | **PASS** |
| `broken_s_10_ration_sum_off.xlsx` | V6 | V6 | YES | **PASS** |
| `broken_s_11_wrong_claim.xlsx` | V5 | V5 | YES | **PASS** |
| `broken_s_12_float_in_int.xlsx` | V1 | V1 | YES | **PASS** |
| `broken_s_13_bad_header.xlsx` | V1 | V1 | YES | **PASS** |
| `broken_s_14_swapped_sheets.xlsx` | V1 | V1 | YES | **PASS** |
| `broken_s_15_v7_delta_penalty.xlsx` | V7 | V7 | YES | **PASS** |
| `broken_m_01_tour_missing_site.xlsx` | V3 | V3,V6 | YES | **PASS** |
| `broken_m_02_repeated_switch_rule.xlsx` | V3 | V3 | YES | **PASS** |
| `broken_m_03_non_consecutive_crate_id.xlsx` | V3 | V1,V3 | YES | **PASS** |
| `broken_m_04_alarm_tick_decreasing.xlsx` | V3 | V3 | YES | **PASS** |
| `broken_m_05_short_serial.xlsx` | V2 | V2 | YES | **PASS** |
| `broken_m_06_window_duration_invalid.xlsx` | V2 | V2 | YES | **PASS** |
| `broken_x_01_trap49_not_repeated.xlsx` | V8 | V5,V8 | YES | **PASS** |

---

## 6. Reproduction Commands

### 1. Validate Full Dataset (`cases.xlsx`)
```bash
python validator/validate.py cases.xlsx
```
*Evaluates all 50 cases in ~17.7 seconds. Exit code 0.*

### 2. Run Test Suite
```bash
python validator/tests/run_tests.py
```
*Validates 3 clean workbooks and rejects all 22 corrupted workbooks. Exit code 0.*

### 3. Generate Master Report
```bash
python validator/generate_report.py
```
*Generates `validation_report.txt` containing full validation output and negative test evidence.*

---

## 7. Submission Readiness & Integrity Assurance
- **Zero Third-Party Packages**: Operates purely on Python 3 standard library and `openpyxl`.
- **Zero Cross-Imports**: `validator/` contains **0 imports** from `generator/`.
- **Full Traceability**: All recomputed values, algorithms, and tests are self-contained and viva-explainable.
