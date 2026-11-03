# LIFELINE Dataset Generator

Algorithmic Relief-Command Engine dataset generator for the LIFELINE world.

## 1. Overview
This module generates the complete 50-case benchmark dataset (`cases.xlsx`) across all 20 sheets as specified in the assignment documentation. It deterministically produces:
- 50 cases (`s-00` to `s-49`): Tier S (`00`–`19`), Tier M (`20`–`39`), Tier L (`40`–`45`), Tier X (`46`–`49`).
- Exactly 20 sheets adhering to the required column schemas and row orderings.
- All six disaster case study signature constraints (Delta Flood, Mountain Earthquake, Coastal Cyclone, Urban Flash Flood, Landslide Corridor, Outbreak Camp).
- The four hostile trap cases (Dock-order, Best-looking-crate, Shortest-looks-cheapest, Near-miss).
- Planted answers (Tour, Vertex Cover, 3-SAT assignment, Ration target).
- Exact optimal claims for the six decision problems on Tier S (0/1 Knapsack, Interval Scheduling count, Interval Scheduling value, Rod Cutting, Held-Karp TSP, Minimum Vertex Cover).
- All variety conditions (suboptimal greedy knapsack, fewest-roads vs cheapest path divergence, safety rule ratios).

## 2. Dependencies
**Zero external dependencies.**
The generator is implemented entirely using Python standard libraries:
- `zipfile`, `xml.sax.saxutils`, `io` (Pure Python OpenXML spreadsheet writer)
- `random`, `math`, `collections`, `heapq`, `itertools`, `argparse`

Requires **Python 3.8+**.

## 3. Reproduction Command
To reproduce the master `cases.xlsx` file using the group seed:

```bash
python3 generator/generate.py --seed 17 --output cases.xlsx
```

### Options
- `--seed <int>`: Group seed $s$ from the group-selection sheet (default: `17`).
- `--output <path>`: Destination path for the generated workbook (default: `cases.xlsx`).

## 4. Architecture
- `generator/generate.py`: Main CLI entry point. Orchestrates case generation across all 50 cases, formats rows according to sheet schemas, and invokes the workbook writer.
- `generator/case_builder.py`: Generates the complete dataset for each case deterministically using `random.Random(seed * 10007 + case_no * 101)`. Enforces all scenario signature rules, variety constraints, and trap specifications.
- `generator/solvers.py`: Exact dynamic programming and graph algorithms used to calculate optimal claims on Tier S and verify counterexamples.
- `generator/writer.py`: Fast, zero-dependency OpenXML `.xlsx` writer that packages standard worksheet XMLs into a compliant spreadsheet archive with deterministic timestamps for byte-identical reproducibility.

