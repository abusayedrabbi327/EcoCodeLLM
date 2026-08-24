# IV. PROPOSED ECOCODE-LLM FRAMEWORK

## A. Framework Overview

`EcoCode-LLM` is a Green AI software engineering framework designed to bridge the gap between functional correctness and runtime energy efficiency in AI-assisted code generation. Rather than treating energy efficiency as a post-hoc measurement or relying on non-deterministic model prompting, `EcoCode-LLM` operates as an automated optimization middleware situated between the LLM output and the production execution environment.

The framework operates on a **dual-mode paradigm**:
1. **Mode 1 (Energy-Aware Generation & Selection):** Solves new programming problems by requesting $N$ candidate code variants from a code-generation LLM using high-temperature sampling, executing automated unit tests to filter out incorrect solutions, profiling valid solutions for execution time, peak memory usage, and energy consumption, and selecting the optimal candidate using a multi-criteria decision engine.
2. **Mode 2 (Post-Generation Code Optimization):** Takes existing AI-generated or human-written Python source code, verifies its functionality against a test suite, parses it into an Abstract Syntax Tree (AST), identifies energy anti-patterns (such as $O(n^2)$ list membership inside loops or string accumulator concatenation), applies deterministic AST refactoring transformations, reconstructs optimized code, and validates that performance and energy efficiency are improved without breaking program behavior.

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                      EcoCode-LLM CLI/GUI                    │
                    └──────────────────────────────┬──────────────────────────────┘
                                                   │
                         ┌─────────────────────────┴─────────────────────────┐
                         ▼                                                   ▼
       ┌───────────────────────────────────┐               ┌───────────────────────────────────┐
       │   Mode 1: Energy-Aware Generation  │               │    Mode 2: Post-Gen Optimization  │
       └─────────────────┬─────────────────┘               └─────────────────┬─────────────────┘
                         │                                                   │
   1. OpenRouter / OpenAI API Code Generator           1. Raw Python Code / AST Parser (`ast_parser.py`)
      ($N$ Candidate Variants via High Temp)                                 │
                         │                             2. Pattern Detector (`pattern_detector.py`)
                         ▼                                (6 Energy Anti-Patterns: R001-R006)
       ┌───────────────────────────────────┐                                 │
       │    Automated Testing Sandbox      │           3. AST Node Transformers (`refactoring_rules.py`)
       │    (`test_runner.py`)             │                                 │
       └─────────────────┬─────────────────┘           4. Code Reconstructor (`code_reconstructor.py`)
                         │ Filter Invalid Code                               │
                         ▼                                                   ▼
       ┌───────────────────────────────────────────────────────────────────────────┐
       │                   Multi-Metric Execution Profiler                         │
       │  • Time Profiler (`time_profiler.py`) — Execution Time (ms)               │
       │  • Memory Profiler (`memory_profiler.py`) — Peak RSS Memory (KB)           │
       │  • Energy Profiler (`energy_profiler.py`) — Intel RAPL / TDP Model (J)      │
       └─────────────────────────────────────┬─────────────────────────────────────┘
                                             │
                                             ▼
       ┌───────────────────────────────────────────────────────────────────────────┐
       │                 TOPSIS Multi-Criteria Decision Engine                     │
       │  • Min-Max Normalizer (`normalizer.py`)                                   │
       │  • Weighted Scoring (`topsis_scorer.py`): 50% Energy + 35% Time + 15% Mem │
       │  • Candidate Reranker (`ranking.py`)                                      │
       └─────────────────────────────────────┬─────────────────────────────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │ Output Optimized Solution │
                               └───────────────────────────┘
```

---

## B. Mode 1: Energy-Aware Code Generation & Candidate Selection

Mode 1 addresses the limitation of single-shot LLM code generation, where models often generate functionally correct but energy-inefficient solutions. 

1. **Stochastic Candidate Generation:** For a natural language prompt $P$, the generator queries the LLM with elevated temperature ($T \approx 0.7$) to produce $N$ distinct code candidates $\{C_1, C_2, \dots, C_N\}$.
2. **Automated Correctness Verification:** Candidates are executed against a validation test suite in an isolated subprocess sandbox. Candidates failing unit tests are disqualified:
   $$\mathcal{C}_{\text{valid}} = \{ C_i \mid \text{TestRunner}(C_i) = \text{PASS} \}$$
3. **Multi-Metric Dynamic Profiling:** Each valid candidate is profiled over multiple execution runs to collect:
   - Execution Time ($T_i$ in milliseconds)
   - Peak RAM Memory ($M_i$ in KB RSS)
   - Energy Consumption ($E_i$ in Joules, measured via Intel RAPL hardware registers or estimated using CPU TDP formula $E_i = \frac{\text{TDP}}{\text{cores}} \times T_i$).
4. **TOPSIS Ranking & Selection:** The decision engine normalizes candidate metrics via Min-Max scaling and computes the Performance Index Score $S_i$:
   $$S_i = w_E \cdot E_{i,\text{norm}} + w_T \cdot T_{i,\text{norm}} + w_M \cdot M_{i,\text{norm}}$$
   where default weights are set to $w_E = 0.50$, $w_T = 0.35$, and $w_M = 0.15$. The candidate with the minimum $S_i$ score (closest to the ideal zero-consumption solution) is selected as the final output.

---

## C. Mode 2: Post-Generation Code Optimization & AST Refactoring

Mode 2 provides a deterministic, rule-based refactoring engine to optimize existing code (whether produced by an LLM, a human developer, or legacy software) without relying on re-prompting.

1. **AST Parsing:** Source code is transformed into an Abstract Syntax Tree (AST) using Python's native `ast` module.
2. **Anti-Pattern Detection:** An AST `NodeVisitor` walks the tree to identify known computational and memory inefficiencies:
   - **R001:** $O(n^2)$ nested loops with list membership (`if item in list_var`).
   - **R002:** String accumulator concatenation inside loop bodies (`str_var += item`).
   - **R003:** Non-vectorized element-wise math in loops.
   - **R004:** File I/O operations (`open()`) executed repeatedly inside loops.
   - **R005:** Redundant `list.append()` inside loops convertible to list comprehensions.
   - **R006:** Frequent global variable reads/writes within tight loops.
3. **Deterministic AST Transformation:** Matching subtrees are transformed using AST `NodeTransformer` rules. For example:
   - *R001 Transformation:* Automatically injects set instantiation (`_set_var = set(list_var)`) prior to the loop and updates the membership check to $O(1)$ set lookup.
   - *R002 Transformation:* Converts string concatenation into list collection (`_parts.append(...)`) followed by `"".join(_parts)`.
4. **Code Reconstruction & Equivalence Validation:** The modified AST is reconstructed back to formatted Python source code using `ast.unparse()`. The rewritten code is executed against the test suite to guarantee functional preservation.
5. **Comparative Benchmarking:** The profiler compares original vs. rewritten implementations, generating detailed percentage improvement metrics for execution time, memory footprint, and energy consumption.

---

## D. System Architecture & Module Implementation Mapping

| Paper Module | Python Module / File | Primary Functions & Responsibilities |
| :--- | :--- | :--- |
| **Generation Engine** | [`ecocode/mode1_selection/generator.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/mode1_selection/generator.py) | Queries OpenRouter/OpenAI APIs to generate $N$ candidate solutions. |
| **Candidate Pool Manager** | [`ecocode/mode1_selection/solution_pool.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/mode1_selection/solution_pool.py) | Tracks candidates, filters by test results, and manages execution pools. |
| **AST Parser & Reconstructor** | [`ecocode/mode2_rewriting/ast_parser.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/mode2_rewriting/ast_parser.py)<br>[`ecocode/mode2_rewriting/code_reconstructor.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/mode2_rewriting/code_reconstructor.py) | Converts source code to AST representation and back to Python source code. |
| **Pattern Detector** | [`ecocode/mode2_rewriting/pattern_detector.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/mode2_rewriting/pattern_detector.py) | AST tree walker identifying energy anti-patterns (R001–R006). |
| **Refactoring Rules Engine** | [`ecocode/mode2_rewriting/refactoring_rules.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/mode2_rewriting/refactoring_rules.py) | Implements AST `NodeTransformer` subclasses for automated optimization. |
| **Correctness & Testing Engine**| [`ecocode/testing/test_runner.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/testing/test_runner.py)<br>[`ecocode/testing/sandbox.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/testing/sandbox.py) | Executes test cases in isolated subprocess sandboxes to verify functional correctness. |
| **Multi-Metric Profiler** | [`ecocode/profiler/time_profiler.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/profiler/time_profiler.py)<br>[`ecocode/profiler/memory_profiler.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/profiler/memory_profiler.py)<br>[`ecocode/profiler/energy_profiler.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/profiler/energy_profiler.py) | Measures execution time (ms), peak RAM (KB), and RAPL hardware or TDP software energy (Joules). |
| **TOPSIS Decision Engine** | [`ecocode/decision_engine/normalizer.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/decision_engine/normalizer.py)<br>[`ecocode/decision_engine/topsis_scorer.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/decision_engine/topsis_scorer.py)<br>[`ecocode/decision_engine/ranking.py`](file:///d:/UIU/14%20trimester/Green/EcoCode/ecocode/decision_engine/ranking.py) | Normalizes metrics and applies TOPSIS weighted scoring ($50\% E, 35\% T, 15\% M$) for candidate ranking. |

---

## E. Gap Analysis & Literature Comparison Matrix

The table below demonstrates how the proposed `EcoCode-LLM` framework addresses the research gaps identified in related literature (corresponding to Table I of the paper draft):

| Reference | Scope / Contribution | Key Limitation | How EcoCode-LLM Fills the Gap |
| :--- | :--- | :--- | :--- |
| **Huang et al. (EFFIBENCH, 2024)** | Evaluates efficiency of LLM-generated code. | Passive benchmarking; no automated code refactoring. | Integrates Mode 2 active AST refactoring to transform inefficient code. |
| **Qiu et al. (2025)** | Benchmarks generated vs. reference code. | No automated post-generation optimization mechanism. | Provides automated code rewriting and multi-metric TOPSIS selection. |
| **Goyal et al. (EnCoDe, 2026)** | Design-time static source code energy estimation. | Estimates energy consumption but does not modify code. | Combines static pattern detection with automated code rewriting and dynamic verification. |
| **Ilager et al. (GREEN-CODE, 2025)** | Early exiting to reduce LLM inference energy. | Optimizes LLM model inference, not program execution cost. | Optimizes runtime resource execution cost of generated code. |
| **Vartziotis et al. / Cappendijk et al.** | Evaluates green prompt engineering techniques. | Prompt effects are stochastic and non-deterministic. | Provides deterministic AST transformations combined with empirical profiling. |
| **Xia et al. (2025)** | Energy-guided candidate reranking. | Only applies to newly generated LLM code. | Supports dual modes: reranking generated candidates (Mode 1) AND optimizing existing human/AI code (Mode 2). |
