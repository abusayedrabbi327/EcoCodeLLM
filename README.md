# 🌿 EcoCode-LLM

**A Green AI Framework for Energy-Efficient Code Generation**

EcoCode-LLM is an automated framework that ensures AI-generated code is not just correct but also energy-efficient. It works as a middleware layer between raw LLM output and production environments.

## Features

- **Mode 1: Generate & Select** — Generates N code variants via LLM, tests all for correctness, profiles survivors for time/memory/energy, and selects the most efficient using TOPSIS scoring.
- **Mode 2: Analyze & Rewrite** — Parses existing code into AST, detects anti-patterns (O(n²) loops, string concatenation, etc.), applies rule-based refactoring, and validates output equivalence.
- **Multi-Metric Profiling** — Measures execution time (ms), peak memory (KB), and energy consumption (J).
- **TOPSIS Decision Engine** — Weighted multi-criteria scoring: Energy (50%) + Time (35%) + Memory (15%).

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up API Key (Mode 1 only)
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Run Mode 1 — Generate & Select
```bash
python -m ecocode.main --mode 1 \
    --prompt "Write a function to find all duplicates in a list" \
    --test-file benchmarks/test_cases/tests_03_find_duplicates.json \
    --output outputs/reports/duplicates_report.json
```

### 4. Run Mode 2 — Analyze & Rewrite
```bash
python -m ecocode.main --mode 2 \
    --input-file benchmarks/problems/sample_unoptimized.py \
    --test-file benchmarks/test_cases/tests_03_find_duplicates.json \
    --output outputs/reports/optimization_report.json
```

## Project Structure

```
EcoCode/
├── ecocode/                    # Core framework
│   ├── main.py                 # CLI entry point
│   ├── mode1_selection/        # Generate & Select pipeline
│   ├── mode2_rewriting/        # Analyze & Rewrite pipeline
│   ├── testing/                # Correctness validation
│   ├── profiler/               # Time, memory, energy measurement
│   ├── decision_engine/        # TOPSIS scoring
│   ├── models/                 # Data classes
│   └── utils/                  # Config, logging, display
├── tests/                      # Unit tests
├── benchmarks/                 # Problem sets & test cases
├── outputs/                    # Generated results
├── config.yaml                 # Configuration
└── requirements.txt            # Dependencies
```

## Configuration

Edit `config.yaml` to adjust:
- LLM provider, model, temperature, and number of candidates
- Profiler settings (energy method, CPU TDP)
- TOPSIS weights for energy, time, and memory
- Output preferences

## Running Tests

```bash
python tests/test_topsis.py
python tests/test_refactoring_rules.py
```

## License

Research project — UIU Green Computing Course.
