# 🔬 EcoCode-LLM: Empirical Replication & Reproducibility Guide

This guide provides step-by-step instructions for independent researchers, reviewers, and evaluators to reproduce all experimental findings, decision rankings, and statistical analyses presented in the manuscript:  
**"EcoCode-LLM: A Green AI Framework for Energy-Efficient Code Generation"**

---

## 🧭 Overview of Reproducibility Tiers

In computer systems and empirical software engineering, reproducibility is structured across two complementary tiers:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          ECOCODE REPRODUCIBILITY ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  TIER 1: Deterministic Data & Artifact Verification (Cross-Platform)            │
│  • Platform: Windows, macOS, Linux (Any PC)                                     │
│  • Duration: ~5 seconds                                                         │
│  • Action: Re-computes TOPSIS scores, deltas, and regenerates all paper tables  │
│    and publication figures directly from verified raw Linux RAPL telemetry.     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  TIER 2: Live Hardware Energy Profiling (Platform-Specific)                     │
│  • Platform: Bare-Metal Linux + Intel CPU with RAPL sysfs access                │
│  • Duration: ~5–10 minutes                                                      │
│  • Action: Reads live MSR counters (/sys/class/powercap/intel-rapl) using loop  │
│    amplification and idle baseline subtraction.                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 1. Environment Setup

### Prerequisites
* Python 3.10+ (Tested on Python 3.12.1 and 3.14.7)
* Recommended: Create an isolated Python virtual environment

```bash
# Clone the repository
git clone https://github.com/abusayedrabbi327/EcoCodeLLM.git
cd EcoCodeLLM

# Install required dependencies
pip install -r 01_product_codebase/requirements.txt
```

---

## ⚡ 2. Tier 1: Instant Paper Artifact & Table Reproduction (Any PC)

You can reproduce **all paper results, mathematical rankings, and publication figures** on any operating system (Windows, macOS, Linux) without requiring specialized hardware telemetry counters.

### Run the Artifact Generator:
```bash
cd 01_product_codebase
python export_all_artifacts_for_paper.py
```

### What this script does:
1. **Parses the Empirical Ground-Truth Data:** Reads [`outputs/real_linux_rapl_results.json`](outputs/real_linux_rapl_results.json), containing the 10-iteration measured distributions (Mean, SD, 95% CI) collected on an Intel Core i3 testbed under Kali Linux.
2. **Executes Classical Vector-Normalized TOPSIS:** Computes Euclidean vector normalization, weighted cost distances ($d^+, d^-$), and relative closeness coefficients ($C_i$) matching Hwang & Yoon (1981).
3. **Outputs Camera-Ready LaTeX Tables:**
   * **Table IV:** Hardware testbed parameters & environmental baseline ($P_{\text{idle}} = 0.9175\text{ W}$).
   * **Table VI:** Mode 1 multi-candidate profiling & TOPSIS rankings (P01 Two Sum, P02 Fibonacci, P03 Find Duplicates).
   * **Table VII:** Mode 2 deterministic AST refactoring gains ($\Delta T, \Delta M, \Delta E$) across distinct unoptimized baselines.
   * **Table VIII:** Mode 1 candidate selection vs. Greedy ($\tau=0.0$) and Random baselines (+81.28% energy saving, 19,566 break-even executions).
   * **Table IX:** Green Rule Catalog specifications, AST rewrite targets, and soundness preconditions (R001–R007).
4. **Regenerates Publication Figures:** Saves reconciled high-resolution plots (`fig_mode1_topsis_radar.png`, `fig_ast_rule_reductions.png`, `fig_workload_scalability.png`, etc.) ensuring 100% agreement between tables and charts.

---

## 🧪 3. Running Unit Tests & Correctness Verification

To verify that the AST refactoring engine preserves semantic behavior and that the TOPSIS decision engine executes correctly:

```bash
cd 01_product_codebase
pytest tests/
```

Expected test coverage:
* `test_topsis.py`: Validates vector normalization, monotonicity, and ranking consistency under varied priority weights.
* `test_refactoring_rules.py`: Validates that deterministic AST rewrites pass 100% of functional test assertions with 0.0% regression.

---

## 🔌 4. Tier 2: Live Hardware RAPL Energy Re-Execution (Linux Intel)

To re-run the physical benchmarking pipeline and collect new hardware power readings from scratch:

### Hardware & OS Requirements
* **Operating System:** Linux (Ubuntu 22.04+, Debian 12+, or Kali Linux)
* **Processor:** Intel Core Processor supporting Running Average Power Limit (RAPL)
* **Kernel Interface:** Access to `/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj`
* **Privileges:** Root/sudo privileges or read permissions to the powercap sysfs directory:
  ```bash
  sudo chmod -R a+r /sys/class/powercap/intel-rapl/
  ```

### Execute the Benchmark Suite:
```bash
cd 01_product_codebase
sudo python benchmarks/linux_rapl_benchmark_suite.py
```

### Key Methodological Safeguards:
1. **Loop Amplification Factor ($K$):** Sub-millisecond executions are repeated within an adaptive loop ($K = 923$ to $50{,}000$ iterations) to ensure execution duration exceeds $>250\text{ ms}$, completely bypassing RAPL's $\sim 1\text{ ms}$ register update tick limit.
2. **Idle Power Compensation:** The quiescent baseline draw ($P_{\text{idle}}$) is measured over a 2.0-second calibration window before benchmarks execute and subtracted from total energy:
   $$E_{\text{net}} = E_{\text{total}} - (P_{\text{idle}} \times \Delta t)$$
3. **Cross-Platform Fallback:** If executed on Windows, macOS, or virtualized environments without physical MSR access, the script automatically logs a notice and activates the calibrated Thermal Design Power (TDP) software estimation proxy:
   $$E_{\text{est}} = \left(\frac{P_{\text{TDP}}}{N_{\text{cores}}}\right) \times \left(\frac{T_{\text{ms}}}{1000}\right)$$

> **Note on Cross-Hardware Variability:** While absolute runtimes (ms) and physical energy ($\mu\text{J}$) will naturally vary across different CPU clock rates and microarchitectures (e.g., an Intel Core i7 will complete workloads faster than an i3), the **relative algorithmic complexity transitions and Pareto rankings** ($O(N)$ dominating $O(N^2)$ by 80–99%) remain strictly invariant.

---

## 🖥️ 5. Running the Interactive Application

EcoCode-LLM includes both a desktop GUI and a web-based interface for interactive code optimization and generation.

### Run Desktop GUI:
```bash
cd 01_product_codebase
python run_ui.py
```

### Run Mode 1 via CLI (Energy-Aware Generation):
```bash
cd 01_product_codebase
python -m ecocode.main --mode 1 \
  --prompt "Write an efficient Python function to find two numbers that sum to target" \
  --test-file benchmarks/test_cases/tests_01_two_sum.json \
  --output outputs/reports/p01_generation_report.json
```

### Run Mode 2 via CLI (Deterministic AST Refactoring):
```bash
cd 01_product_codebase
python -m ecocode.main --mode 2 \
  --input-file benchmarks/problems/sample_unoptimized.py \
  --test-file benchmarks/test_cases/tests_01_two_sum.json \
  --output outputs/reports/p01_refactoring_report.json
```

---

## 📄 Primary Telemetry Artifacts

All raw experimental logs used in the manuscript are permanently preserved in the repository:
* [`outputs/real_linux_rapl_results.json`](outputs/real_linux_rapl_results.json): Contains machine metadata, idle power calibration, 10-run mean/SD/CI values, loop amplification factors ($K$), and raw microjoule telemetry for all Mode 1 and Mode 2 evaluations.
