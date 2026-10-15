# 🌿 EcoCode-LLM: A Green AI Framework for Energy-Efficient Code Generation & Optimization

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Hardware Telemetry](https://img.shields.io/badge/Telemetry-Intel%20RAPL%20MSR%20%2B%20TDP-brightgreen.svg)]()
[![Decision Model](https://img.shields.io/badge/MCDM-Classical%20Vector%20TOPSIS-orange.svg)]()
[![Functional Safety](https://img.shields.io/badge/Regression-0.0%25%20Verified-success.svg)]()
[![License](https://img.shields.io/badge/License-Strict%20Academic%20Research-red.svg)](LICENSE)

EcoCode-LLM is a Green AI middleware framework designed to make **energy consumption, runtime latency, and peak memory utilization** first-class software quality criteria in AI-assisted software development. Rather than modifying or retraining underlying Large Language Models (LLMs), EcoCode-LLM wraps model interactions with an automated validation, dynamic hardware profiling, and Abstract Syntax Tree (AST) rewriting pipeline.

---

## 📌 Quick Links for Reviewers & Supervisors
* 📑 **[Peer Reviewer & Supervisor Validation Guide](REVIEWER_GUIDE.md)** — Step-by-step claim-to-evidence audit, table reproduction, and physics verification.
* 🔬 **[Reproducibility & Replication Guide](REPRODUCIBILITY.md)** — Two-tier replication guide, hardware requirements, and baseline benchmarks.
* ⚖️ **[Strict Academic Research License](LICENSE)** — Terms of use, non-commercial research clause, and attribution requirements.

---

## 💡 The Core Problem & Motivation

Modern code-generation frontier models (such as GPT-4, Claude, and Qwen) focus heavily on functional pass rates and syntactic validity. However, benchmark studies demonstrate that:
1. **Functional correctness does not imply resource efficiency:** Generated code frequently exhibits quadratic loops ($O(N^2)$), redundant allocations, or unbuffered I/O.
2. **Greedy decoding is energy-blind:** Default sampling strategies often miss Pareto-optimal implementations that consume substantially less energy.
3. **Inference greening vs. execution greening:** Optimizing model token generation (e.g., early exiting) does not diminish the energy consumed by the generated software across repeated production executions.

EcoCode-LLM bridges this gap through a closed-loop dual-mode middleware architecture.

---

## 🏛️ Framework Architecture

```text
                               ┌────────────────────────┐
                               │ User / Developer Input │
                               └───────────┬────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
       [Mode 1: Code Generation]                     [Mode 2: Code Refactoring]
       Natural Language Problem                       Existing Python Source Code
                    │                                             │
                    ▼                                             ▼
         LLM Candidate Sampler                         AST Parser & Complexity Analyzer
       (N=3 Candidates, tau=0.7)                     (Syntax Trees & Anti-Pattern Detection)
                    │                                             │
                    ▼                                             ▼
       Automated Sandbox Testing                      Green Rule Engine (R001–R007)
         (Functional Gate V_i)                         (Deterministic Tree Rewriting)
                    │                                             │
                    ▼                                             ▼
       Tri-Metric Hardware Profiler                  Regression Invariant Testing
      (Latency T, Memory M, Energy E)                  (Semantic Equivalence Gate)
                    │                                             │
                    ▼                                             ▼
       Classical TOPSIS Selection                    Non-Inferiority Pareto Filter
        (Vector Normalized MCDM)                     (ΔE > 0, ΔT >= 0, ΔM >= -δ_tol)
                    │                                             │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                           ┌───────────────────────────────┐
                           │   Deployment-Ready Solution   │
                           │  Verified Correct & Optimal   │
                           └───────────────────────────────┘
```

### Operational Modes:
* **Mode 1 (Energy-Aware Code Generation):** Ingests programming task specifications, stochastically samples multiple candidate solutions ($N=3$, $\tau=0.7$), executes automated correctness testing in an isolated subprocess sandbox, profiles survivors across three dimensions ($T, M, E$), and selects the Pareto-optimal candidate using **Classical Vector-Normalized TOPSIS** (+81.28% energy savings over random selection).
* **Mode 2 (Existing Code Optimization):** Ingests existing or AI-generated Python code, parses it into an Abstract Syntax Tree (AST), identifies computational energy smells via a formal **Green Rule Catalog (R001–R007)**, executes deterministic syntax rewrites, and commits changes only upon passing unit tests and memory bounds (57.0% latency and 58.4% energy reductions with 0.0% functional regression).

---

## 🚀 Complete Running Process & Getting Started

### 1. Prerequisites & Installation

Clone the repository and install the dependencies in an isolated virtual environment:

```bash
# Clone repository
git clone https://github.com/abusayedrabbi327/EcoCodeLLM.git
cd EcoCodeLLM

# Create virtual environment
python -m venv .venv

# Activate environment (Linux/macOS)
source .venv/bin/activate
# Or on Windows PowerShell:
# .venv\Scripts\Activate.ps1

# Install requirements
pip install -r 01_product_codebase/requirements.txt
```

---

### 2. Configuration & API Keys

Copy the sample environment file and add your OpenRouter or OpenAI API key (required **only** for live Mode 1 generation):

```bash
cp 01_product_codebase/.env.example 01_product_codebase/.env
```
Open `01_product_codebase/.env` in your text editor and provide your key:
```ini
OPENROUTER_API_KEY=sk-or-v1-your_actual_key_here
```

Framework parameters (candidate count $N$, timeout, and TOPSIS weights $w_E=0.50, w_T=0.35, w_M=0.15$) can be configured in [`01_product_codebase/config.yaml`](01_product_codebase/config.yaml).

---

### 3. Rapid Empirical Artifact Replication (Any PC)

To reproduce **all paper results, mathematical rankings, and publication figures** from our verified Linux Intel RAPL raw data in ~5 seconds:

```bash
python 01_product_codebase/export_all_artifacts_for_paper.py
```
This prints the exact LaTeX tables (Tables IV, VI, VII, VIII, IX) and regenerates all figures matching the manuscript.

---

### 4. Running Mode 1 via CLI (Energy-Aware Generation)

To generate multiple implementations for a programming problem, profile them, and select the optimal green candidate:

```bash
cd 01_product_codebase
python -m ecocode.main --mode 1 \
  --prompt "Write an efficient Python function to find two numbers that sum to target" \
  --test-file benchmarks/test_cases/tests_01_two_sum.json \
  --output outputs/reports/two_sum_report.json
```

---

### 5. Running Mode 2 via CLI (AST Optimization)

To analyze and deterministically refactor an unoptimized Python script:

```bash
cd 01_product_codebase
python -m ecocode.main --mode 2 \
  --input-file benchmarks/problems/sample_unoptimized.py \
  --test-file benchmarks/test_cases/tests_03_find_duplicates.json \
  --output outputs/reports/optimization_report.json
```

---

### 6. Running Interactive Applications

EcoCode-LLM provides two intuitive user interfaces:

#### Desktop GUI (Tkinter Launcher)
```bash
# Run from repository root
python run_ui.py
```

#### Web Application (Streamlit Dashboard)
```bash
cd 01_product_codebase
streamlit run app_professional.py
```

---

### 7. Running the Automated Test Suite

To run the complete unit test harness verifying TOPSIS arithmetic and AST refactoring rules:

```bash
cd 01_product_codebase
pytest tests/ -v
```

---

### 8. Live Hardware Energy Benchmarking (Linux Intel Bare-Metal)

On an Intel CPU running bare-metal Linux with RAPL interface access:

```bash
cd 01_product_codebase
sudo python benchmarks/linux_rapl_benchmark_suite.py
```
*(On Windows or macOS, this script automatically falls back to the calibrated TDP software estimation model).*

---

## 📂 Repository Structure

```text
EcoCodeLLM/
├── README.md                           # Main Project Overview & Running Guide
├── REVIEWER_GUIDE.md                   # Peer Reviewer Claim-to-Evidence Audit Manual
├── REPRODUCIBILITY.md                  # Two-Tier Replication Instructions
├── LICENSE                             # Strict Academic Research License
├── run_ui.py                           # Root launcher for desktop GUI
│
└── 01_product_codebase/
    ├── config.yaml                     # Framework hyperparameters and MCDM weights
    ├── requirements.txt                 # Python dependencies
    ├── .env.example                    # Safe environment template
    ├── app.py & app_professional.py    # Streamlit interactive web interfaces
    ├── gui.py & gui_professional.py    # Desktop GUI interfaces
    ├── export_all_artifacts_for_paper.py# One-click artifact & table generator
    ├── generate_all_paper_artifacts.py # Figure/table synchronization script
    │
    ├── benchmarks/
    │   ├── linux_rapl_benchmark_suite.py # Physical Intel RAPL profiling harness
    │   ├── problems/                   # Benchmark problem snippets
    │   └── test_cases/                 # JSON test suites (P01, P02, P03)
    │
    ├── ecocode/                        # Core Engine Package
    │   ├── main.py                     # CLI routing and controller
    │   ├── decision_engine/            # Classical Vector TOPSIS scoring
    │   ├── mode1_selection/            # Multi-candidate generation & gating
    │   ├── mode2_rewriting/            # AST parser & Green Rules (R001–R007)
    │   ├── profiler/                   # Tri-metric time, memory & RAPL profilers
    │   ├── testing/                    # Isolated subprocess sandbox
    │   └── utils/                      # Logging, display, and config utilities
    │
    ├── outputs/
    │   └── real_linux_rapl_results.json# Verified 10-run Linux RAPL telemetry logs
    │
    └── tests/                          # Automated regression test suite
        ├── test_topsis.py
        ├── test_new_topsis.py
        └── test_refactoring_rules.py
```

---

<!-- ## 📜 Academic Citation & Attribution

If you use EcoCode-LLM in your academic research or reference its methodology, please cite:

```bibtex
@article{rabbi2026ecocode,
  title={EcoCode-LLM: A Green AI Framework for Energy-Efficient Code Generation},
  author={Rabbi, Abu Sayed and Samiha, Maisha and Islam, Md. Motaharul},
  journal={Department of Computer Science and Engineering, United International University},
  year={2026}
} -->
```

---

## ⚖️ License
This project is governed under a **Strict Academic Research & Proprietary License**. It is strictly intended for academic review, scientific validation, and peer evaluation. Commercial use, unauthorized redistribution, and training AI models on this codebase are strictly prohibited without prior written consent. See [`LICENSE`](LICENSE) for complete terms.
