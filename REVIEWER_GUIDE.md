# 📑 EcoCode-LLM: Peer Reviewer & Supervisor Validation Guide

**A Line-by-Line Claim-to-Evidence Verification Manual for Manuscript Evaluation**  
**Associated Manuscript:** *EcoCode-LLM: A Green AI Framework for Energy-Efficient Code Generation*  
**Repository:** [https://github.com/abusayedrabbi327/EcoCodeLLM](https://github.com/abusayedrabbi327/EcoCodeLLM)

---

## 🎯 Purpose of This Guide

This document is prepared specifically for **peer reviewers**, **journal editors**, and **academic supervisors** to provide transparent, rigorous, and verifiable access to the evidence base underlying EcoCode-LLM.

It enables you to:
1. **Audit every numerical claim, table, and figure** in the manuscript in under 10 seconds.
2. **Inspect the raw hardware telemetry logs** collected on our Linux bare-metal Intel testbed.
3. **Verify the mathematical decision engine** (Classical Vector-Normalized TOPSIS).
4. **Inspect the formal AST refactoring specifications and preconditions** (R001–R007).
5. **Re-execute live benchmarking** under controlled hardware conditions.

---

## ⚡ 1. Rapid 10-Second Artifact Audit (Any PC — Windows / macOS / Linux)

Reviewers can verify that all paper numbers are generated directly from verified empirical logs without needing a Linux/Intel testbed:

```bash
# Clone the repository
git clone https://github.com/abusayedrabbi327/EcoCodeLLM.git
cd EcoCodeLLM

# Install lightweight dependencies
pip install -r 01_product_codebase/requirements.txt

# Run the 1-click artifact and table generator
python 01_product_codebase/export_all_artifacts_for_paper.py
```

### Expected Output:
The script parses the ground-truth telemetry in `01_product_codebase/outputs/real_linux_rapl_results.json`, calculates Classical Vector-Normalized TOPSIS distances, and prints camera-ready LaTeX code for **Tables IV, VI, VII, VIII, and IX**, while regenerating publication-grade figures.

---

## 📊 2. Manuscript Claim-to-Evidence Audit Matrix

The table below maps every empirical claim in the paper to the exact source script and data entry:

| Paper Element | Claim in Manuscript | Empirical Evidence / Data Source | How to Verify |
|---|---|---|---|
| **Table IV** | Hardware testbed: Intel i3-7020U, 4 threads, 3.71 GB RAM, Kali Linux kernel 6.8.11, Python 3.12.1, $P_{\text{idle}} = 0.9175\text{ W}$. | [`real_linux_rapl_results.json:L2-L15`](01_product_codebase/outputs/real_linux_rapl_results.json#L2-L15) | Inspect JSON metadata section; values captured directly via `lscpu` and `/proc/cpuinfo`. |
| **Table VI** | Mode 1 Candidates: C1.1 ($61.0\,\mu\text{J}, 0.0156\text{ ms}, C_1 = 0.9998$) dominates C1.2 and C1.3 ($827.7\,\mu\text{J}$). | [`real_linux_rapl_results.json:L16-L105`](01_product_codebase/outputs/real_linux_rapl_results.json#L16-L105) | Run `export_all_artifacts_for_paper.py`. Verify $x'_T, x'_M, x'_E$ Euclidean vector normalization and closeness scores ($C_i$). |
| **Table VII** | Mode 2 AST Refactoring: Achieves **57.0% latency reduction** and **58.4% physical energy reduction** with **0.0% regression**. | [`real_linux_rapl_results.json:L140-L215`](01_product_codebase/outputs/real_linux_rapl_results.json#L140-L215) | Compare original baseline vs refactored metrics across P01, P02, P03, and String Concat (R002). |
| **Table VIII** | TOPSIS multi-criteria selection saves **+81.28% energy** over random selection; inference break-even is **19,566 executions**. | [`real_linux_rapl_results.json:L106-L139`](01_product_codebase/outputs/real_linux_rapl_results.json#L106-L139) | Check Table VIII printout: Greedy ($61.01\,\mu\text{J}$) vs Random Monte Carlo ($325.95\,\mu\text{J}$) vs Worst-case ($827.65\,\mu\text{J}$). |
| **Table IX** | Formal Green Rule Catalog with explicit target AST matching subtrees and soundness preconditions. | [`refactoring_rules.py`](01_product_codebase/ecocode/mode2_rewriting/refactoring_rules.py) & Table IX in LaTeX output | Check rules R001–R007: hashability constraints, variable immutability, generator linear consumption. |
| **Fig. 13 & 14** | Bar charts and before/after profiling comparison matching Table VII to 0.0% variance. | Re-rendered via matplotlib directly from NumPy arrays in `export_all_artifacts_for_paper.py`. | Compare generated plots against manuscript figures. |

---

## 🔬 3. Telemetry Fidelity & Physics Safeguards

Systems reviewers often raise legitimate questions regarding the fidelity of software energy telemetry. Below are the physical and architectural safeguards implemented in EcoCode-LLM:

### 1. Overcoming the Intel RAPL Update Quantum
* **The Hardware Constraint:** Intel RAPL Model-Specific Registers (MSRs) update roughly once every $\sim 1\text{ ms}$, with an internal hardware quantum of $15.3\text{--}61\,\mu\text{J}$ per tick. Micro-benchmark runtimes ($<0.3\text{ ms}$) cannot be sampled directly by RAPL without signal degradation.
* **Our Solution:** EcoCode-LLM deploys an **Adaptive Loop Amplification Harness** ($K = 923$ to $50{,}000$ iterations) inside [`linux_rapl_benchmark_suite.py`](01_product_codebase/benchmarks/linux_rapl_benchmark_suite.py#L320-L331). The workload is amplified until total duration exceeds $>250\text{ ms}$, allowing hundreds of physical RAPL ticks to be integrated accurately. The total microjoules are then divided by $K$.

### 2. Quiescent Idle Power Calibration & Subtraction
* Total raw energy recorded over time window $\Delta t$ includes background OS activity:
  $$E_{\text{net}} = E_{\text{RAPL}} - (P_{\text{idle}} \times \Delta t)$$
* The suite measures $P_{\text{idle}}$ over a 2.0-second quiescent sleep window before benchmarking ($P_{\text{idle}} = 0.9175\text{ W}$ on our testbed).

### 3. Independence of Energy and Runtime ($E \neq c \cdot T$)
* Because native MSR counters reflect dynamic CPU frequency scaling and execution power dissipation, the ratio $E/T$ is physically non-constant in our data:
  * **Candidate C1.1 (Hash Map):** $61.01\,\mu\text{J} / 0.0156\text{ ms} = \mathbf{3911.06\,\mu\text{J/ms}}$
  * **Candidate C1.2 (Two-Pointer):** $89.18\,\mu\text{J} / 0.0273\text{ ms} = \mathbf{3266.81\,\mu\text{J/ms}}$
  * **Candidate C1.3 (Brute-Force):** $827.65\,\mu\text{J} / 0.2708\text{ ms} = \mathbf{3056.32\,\mu\text{J/ms}}$
* Consequently, vector-normalized energy ($x'_E$) is non-collinear with vector-normalized time ($x'_T$), ensuring the TOPSIS multi-criteria engine performs genuine multi-objective trade-off analysis.

---

## 🛡️ 4. Semantic Preservation & Safety Preconditions

Reviewers frequently question whether automated AST transformations risk breaking Python semantics. Mode 2 enforces a **dual-layer safety architecture**:

1. **Precondition Gating (Table IX):**
   * **Rule R001 (Membership Set Conversion):** Requires target elements to implement `__hash__` and verifies collection immutability inside the loop body.
   * **Rule R002 (String Buffer Accumulation):** Requires accumulator initialization to `""` and verifies no intermediate reads occur inside loop iterations.
   * **Rule R004 (Hoisting File I/O):** Verifies file path is invariant and handles file pointer closure outside the loop.
   * **Rule R006 (Generator Pipeline):** Verifies the consumer consumes the iterable linearly with no downstream `len()` or random indexing.
2. **Post-Transformation Test Harness:**
   * Transformed code is immediately executed against the benchmark functional test suite inside an isolated subprocess sandbox.
   * If even a single assertion fails or an unexpected exception is raised, the refactored code is **instantly rejected**, and the original baseline is retained ($0.0\%$ functional regression).

---

## 💻 5. Live Benchmarking Re-Execution (Bare-Metal Linux)

To re-run the benchmark suite live from physical hardware counters:

### Hardware Testbed Prerequisites
* OS: Linux (Ubuntu 22.04 LTS, Debian 12, or Kali Linux)
* CPU: Intel Core processor (Skylake or newer)
* Interface: `/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj`
* Root permissions:
  ```bash
  sudo chmod -R a+r /sys/class/powercap/intel-rapl/
  ```

### Run Benchmark Suite:
```bash
cd 01_product_codebase
sudo python benchmarks/linux_rapl_benchmark_suite.py
```

> **Note on Cross-Hardware Execution:** Running this script on Windows or macOS will automatically trigger the calibrated TDP software fallback model ($E_{\text{est}} = (P_{\text{TDP}} / N_{\text{cores}}) \times T_{\text{ms}}$) as documented in Section IV-A-3b. When run on different Intel Linux processors, absolute milliseconds and microjoules will scale with the CPU clock rate, but the **relative efficiency gains ($O(N)$ vs $O(N^2)$) and Pareto rankings remain invariant**.

---

## 🧪 6. Automated Unit Test Verification

To run the automated test suite confirming TOPSIS normalization and AST transformation rules:

```bash
cd 01_product_codebase
pytest tests/ -v
```

All test cases verify:
* Classical Vector Normalization geometry and closeness bounds ($C_i \in [0, 1]$).
* Monotonic ranking consistency under priority weight shifts.
* AST rule equivalence across syntax-driven edge cases.
