# 🌿 EcoCode-LLM: Architecture & Methodology Diagrams

Comprehensive technical specification and standard architectural diagrams for **EcoCode-LLM** — an automated Green AI optimization framework for energy-efficient code generation and refactoring.

---

## Table of Contents
1. [Diagram 1: Proposed Framework & Methodology](#1-proposed-framework--methodology)
2. [Diagram 2: System Architecture](#2-system-architecture)
3. [Diagram 3: End-to-End Execution Flowchart](#3-end-to-end-execution-flowchart)
4. [Diagram 4: Component Interaction Sequence Flow](#4-component-interaction-sequence-flow)
5. [Diagram 5: TOPSIS Decision Engine Formulation](#5-topsis-decision-engine-formulation)
6. [Supported AST Energy Optimization Rules (Mode 2)](#6-supported-ast-energy-optimization-rules-mode-2)

---

## 1. Proposed Framework & Methodology

### 1.1 Methodology Pipeline Diagram

```mermaid
flowchart TD
    subgraph INPUT [" Phase 1: Problem Input "]
        IN_M1["Natural Language Prompt\n(Problem Description + Specs)"]
        IN_M2["Existing Source Code\n(Python Script / Function)"]
        TC["Test Case Suite\n(JSON Input/Expected Outputs)"]
    end

    subgraph GEN_PARSE [" Phase 2: Candidate Generation & AST Parsing "]
        direction TB
        LLM["LLM Code Generator\n(High-Temperature Sampling: N Candidates)"]
        AST["AST Parser & Pattern Detector\n(AST Visitor: Detect Anti-Patterns R001-R006)"]
        TRANS["AST Refactoring Engine\n(Deterministic Tree Transformations)"]
        RECON["Code Reconstructor\n(Unparse AST to Optimized Python Source)"]
    end

    subgraph VALIDATION [" Phase 3: Correctness Verification "]
        SB["Subprocess Test Sandbox\n(Isolation, Timeout & Resource Limits)"]
        FILTER{"Correctness Gate\nPass all test cases?"}
        DISCARD["Disqualified Candidates\n(Syntax/Runtime/Assertion Failure)"]
        SURVIVORS["Validated Candidate Pool\n(100% Functionally Equivalent)"]
    end

    subgraph PROFILING [" Phase 4: Multi-Metric Execution Profiling "]
        direction TB
        TP["Time Profiler\n(High-res monotonic perf_counter_ns)"]
        MP["Memory Profiler\n(tracemalloc Peak RSS in KB)"]
        EP["Energy Profiler\n(Hardware RAPL / TDP-based Model in Joules)"]
        AGG["Profile Aggregator\n(Multi-run statistical stabilization)"]
    end

    subgraph DECISION [" Phase 5: Multi-Criteria Decision Engine "]
        NORM["Min-Max Metric Normalization\n(Vector scaling to [0, 1])"]
        TOPSIS["TOPSIS Scorer\n(Weighted Distance to Ideal Best)"]
        RANK["Pareto Optimal Selection\n(Rank by Ascending Performance Index S_i)"]
    end

    subgraph OUTPUT [" Output Layer "]
        BEST["Energy-Optimal Solution\n(Source Code + Performance Delta Report)"]
    end

    %% Flow connections
    IN_M1 --> LLM
    IN_M2 --> AST
    AST --> TRANS --> RECON
    TC --> SB

    LLM --> SB
    RECON --> SB
    IN_M2 -.->|Baseline Verification| SB

    SB --> FILTER
    FILTER -- Failed --> DISCARD
    FILTER -- Passed --> SURVIVORS

    SURVIVORS --> TP & MP & EP
    TP & MP & EP --> AGG

    AGG --> NORM --> TOPSIS --> RANK
    RANK --> BEST

    %% Styling
    classDef inputStyle fill:#0f2d2e,stroke:#00e5a0,stroke-width:1.5px,color:#e8f5f0;
    classDef procStyle fill:#132238,stroke:#00c9d4,stroke-width:1.5px,color:#e8f5f0;
    classDef testStyle fill:#1c2d1b,stroke:#7fff5f,stroke-width:1.5px,color:#e8f5f0;
    classDef profStyle fill:#2e2410,stroke:#ffb84d,stroke-width:1.5px,color:#e8f5f0;
    classDef decStyle fill:#28153b,stroke:#a78bfa,stroke-width:1.5px,color:#e8f5f0;
    classDef outStyle fill:#0a3828,stroke:#00e5a0,stroke-width:2px,color:#ffffff;
    classDef errStyle fill:#381313,stroke:#ff6b6b,stroke-width:1.5px,color:#ff9999;

    class IN_M1,IN_M2,TC inputStyle;
    class LLM,AST,TRANS,RECON procStyle;
    class SB,FILTER,SURVIVORS testStyle;
    class DISCARD errStyle;
    class TP,MP,EP,AGG profStyle;
    class NORM,TOPSIS,RANK decStyle;
    class BEST outStyle;
```

### 1.2 Methodological Phases Overview

| Phase | Component | Input | Primary Operation | Output |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | Problem Specification | Prompt / Source File, Tests | Load YAML configurations, parse CLI arguments, and ingest test cases. | Structured Problem Definition |
| **Phase 2** | Code Generation / AST Parse | Prompt / Python Code | **Mode 1**: Stochastic LLM sampling ($N$ variants).<br>**Mode 2**: AST node traversal & pattern detection. | Raw Source Code Pool / Refactored AST |
| **Phase 3** | Correctness Verification | Code Variants, Test Suite | Execution in dedicated subprocess sandbox with timeout traps. | Valid Functional Solutions Pool |
| **Phase 4** | Multi-Metric Profiling | Valid Candidates | Isolate execution across $k$ warmups + $m$ timed runs: Time (ms), RAM (KB), Energy (J). | Raw Multi-Metric Matrix $\mathbf{X}$ |
| **Phase 5** | Decision & Selection | Profile Matrix $\mathbf{X}$ | Min-Max normalization followed by weighted TOPSIS distance calculation. | Optimal Solution & Delta Metrics |

---

## 2. System Architecture

### 2.1 Layered Modular Architecture Diagram

```mermaid
flowchart TB
    subgraph L_UI [" 1. Presentation & Interface Layer "]
        CLI["CLI Interface\n(ecocode.main via Click)"]
        GUI["Desktop GUI\n(Tkinter / CustomTkinter)"]
    end

    subgraph L_CORE [" 2. Pipeline Orchestration Layer "]
        M1_SEL["Mode 1 Selector\n(ecocode.mode1_selection.selector)"]
        M2_ENG["Mode 2 Rewriting Engine\n(ecocode.mode2_rewriting)"]
        POOL["Solution Pool Manager\n(ecocode.mode1_selection.solution_pool)"]
    end

    subgraph L_GEN [" 3. Generation & Refactoring Subsystems "]
        direction LR
        subgraph S_M1 [" Mode 1: LLM Engine "]
            LLM_GEN["Prompt Builder &\nLLM Client (OpenAI/OpenRouter)"]
        end
        subgraph S_M2 [" Mode 2: AST Rule Engine "]
            AST_P["AST Parser\n(ast.parse)"]
            PAT_D["Pattern Detector\n(Rules R001-R006)"]
            REF_R["AST Transformers\n(NodeTransformer)"]
            REC_C["Code Reconstructor\n(astunparse)"]
        end
    end

    subgraph L_TEST [" 4. Execution Sandbox & Verification Layer "]
        TRUN["Test Suite Runner\n(ecocode.testing.test_runner)"]
        SB_EXEC["Subprocess Sandbox\n(ecocode.testing.sandbox)"]
    end

    subgraph L_PROF [" 5. Multi-Dimensional Profiling Subsystem "]
        direction TB
        T_PROF["Time Profiler\n(time_profiler.py)"]
        M_PROF["Memory Profiler\n(memory_profiler.py)"]
        E_PROF["Energy Profiler\n(energy_profiler.py)"]
        P_AGG["Profile Aggregator\n(profile_aggregator.py)"]
    end

    subgraph L_DEC [" 6. Multi-Criteria Decision Engine "]
        NORM["Normalizer\n(normalizer.py)"]
        TOPSIS["TOPSIS Scorer\n(topsis_scorer.py)"]
        RANK["Candidate Ranking\n(ranking.py)"]
    end

    subgraph L_CROSS [" 7. Cross-Cutting Utilities & Models "]
        MODELS["Data Models\n(CodeCandidate, ProfileResult, EvaluationReport)"]
        CFG["Config Loader\n(YAML Config Manager)"]
        LOGGER["Structured Logger\n(Colorized Log Streamer)"]
        FUTILS["File & AST Utilities\n(IO & Cleansing)"]
    end

    subgraph L_OUT [" 8. Artifacts & Reporting Layer "]
        JSON_OUT["Evaluation Report\n(outputs/reports/*.json)"]
        CODE_OUT["Optimized Python Code\n(outputs/optimized_code.py)"]
    end

    %% Inter-layer linkages
    CLI --> M1_SEL & M2_ENG
    GUI --> M1_SEL & M2_ENG

    M1_SEL --> LLM_GEN --> POOL
    M2_ENG --> AST_P --> PAT_D --> REF_R --> REC_C

    POOL --> TRUN
    REC_C --> TRUN
    TRUN --> SB_EXEC

    TRUN --> P_AGG
    P_AGG --> T_PROF & M_PROF & E_PROF

    P_AGG --> NORM --> TOPSIS --> RANK

    RANK --> JSON_OUT & CODE_OUT

    L_CROSS -.-> L_CORE
    L_CROSS -.-> L_GEN
    L_CROSS -.-> L_TEST
    L_CROSS -.-> L_PROF
    L_CROSS -.-> L_DEC

    %% Styling
    classDef uiLayer fill:#0f1d24,stroke:#00c9d4,stroke-width:1.5px,color:#e8f5f0;
    classDef coreLayer fill:#132630,stroke:#00e5a0,stroke-width:1.5px,color:#e8f5f0;
    classDef genLayer fill:#17223b,stroke:#a78bfa,stroke-width:1.5px,color:#e8f5f0;
    classDef testLayer fill:#162b1e,stroke:#7fff5f,stroke-width:1.5px,color:#e8f5f0;
    classDef profLayer fill:#2e2410,stroke:#ffb84d,stroke-width:1.5px,color:#e8f5f0;
    classDef decLayer fill:#291438,stroke:#d946ef,stroke-width:1.5px,color:#e8f5f0;
    classDef utilLayer fill:#1f2937,stroke:#64748b,stroke-width:1.5px,color:#94a3b8;
    classDef outLayer fill:#0a3828,stroke:#00e5a0,stroke-width:2px,color:#ffffff;

    class CLI,GUI uiLayer;
    class M1_SEL,M2_ENG,POOL coreLayer;
    class LLM_GEN,AST_P,PAT_D,REF_R,REC_C genLayer;
    class TRUN,SB_EXEC testLayer;
    class T_PROF,M_PROF,E_PROF,P_AGG profLayer;
    class NORM,TOPSIS,RANK decLayer;
    class MODELS,CFG,LOGGER,FUTILS utilLayer;
    class JSON_OUT,CODE_OUT outLayer;
```

---

## 3. End-to-End Execution Flowchart

### 3.1 Detailed Algorithmic Control Flow

```mermaid
flowchart TD
    START(["Start Execution"]) --> INIT["Load configuration (config.yaml)\nInitialize logger & parse CLI/GUI inputs"]
    INIT --> CHECK_MODE{"Evaluation Mode?"}

    %% ---------------- MODE 1 BRANCH ----------------
    CHECK_MODE -- "Mode 1 (Generation)" --> M1_PROMPT{"Prompt & Test File\nprovided?"}
    M1_PROMPT -- No --> ERR_M1_PARAM["Raise Parameter Error"] --> TERMINATE(["Aborted"])
    M1_PROMPT -- Yes --> M1_LLM["Send System Prompt to LLM API\nSample N candidates at temperature T=0.7"]
    M1_LLM --> M1_API_OK{"API Call\nSuccessful?"}
    M1_API_OK -- No --> ERR_API["Log API Failure"] --> TERMINATE
    M1_API_OK -- Yes --> M1_CLEAN["Strip Markdown wrappers\nExtract executable Python functions"]
    M1_CLEAN --> M1_LOAD_TESTS["Load Test Suite from JSON"]
    M1_LOAD_TESTS --> M1_TEST_LOOP[/"Iterate each Candidate C_i"/]

    M1_TEST_LOOP --> M1_SANDBOX["Execute in Isolated Subprocess\nInject input args -> Validate return value"]
    M1_SANDBOX --> M1_PASS{"Passed 100%\nTest Cases?"}
    M1_PASS -- No --> M1_FAIL_LOG["Mark is_valid = False\nRecord traceback"]
    M1_PASS -- Yes --> M1_PASS_LOG["Mark is_valid = True\nAdd to Valid Pool"]

    M1_FAIL_LOG --> M1_NEXT{"More\ncandidates?"}
    M1_PASS_LOG --> M1_NEXT
    M1_NEXT -- Yes --> M1_TEST_LOOP
    M1_NEXT -- No --> M1_CHECK_SURVIVORS{"Valid Pool\nSize > 0?"}

    M1_CHECK_SURVIVORS -- No --> ERR_NO_VALID["Error: No candidates passed test suite"] --> TERMINATE
    M1_CHECK_SURVIVORS -- Yes --> PROFILE_STAGE

    %% ---------------- MODE 2 BRANCH ----------------
    CHECK_MODE -- "Mode 2 (Refactoring)" --> M2_INPUT{"Source File & Test File\nprovided?"}
    M2_INPUT -- No --> ERR_M2_PARAM["Raise Parameter Error"] --> TERMINATE
    M2_INPUT -- Yes --> M2_READ["Read Source Code File"]
    M2_READ --> M2_VERIFY_ORIG["Run Original Code against Test Suite"]
    M2_VERIFY_ORIG --> M2_ORIG_PASS{"Original Code\nPasses Tests?"}
    M2_ORIG_PASS -- No --> ERR_ORIG_FAIL["Error: Baseline code fails test suite.\nCannot refactor unsafe code."] --> TERMINATE

    M2_ORIG_PASS -- Yes --> M2_PARSE["Parse Source to AST (ast.parse)"]
    M2_PARSE --> M2_PARSE_OK{"Valid Python\nAST?"}
    M2_PARSE_OK -- No --> ERR_AST["Error: Syntax parse failure"] --> TERMINATE

    M2_PARSE_OK -- Yes --> M2_DETECT["Traverse AST with Rule Detectors\n(R001: Quadratic loops, R002: Str concat,\nR003: Redundant calls, R004: Inefficient lookups)"]
    M2_DETECT --> M2_HAS_PATTERNS{"Anti-Patterns\nFound?"}

    M2_HAS_PATTERNS -- No --> M2_NO_OP["Log: Code is already optimal\nProfile original code only"] --> M2_SOLO_PROFILE["Profile Original"] --> WRITE_OUTPUT
    M2_HAS_PATTERNS -- Yes --> M2_APPLY_RULES["Apply AST Node Transformers\n(refactoring_rules.py)"]
    M2_APPLY_RULES --> M2_RECON["Reconstruct Source Code (astunparse)"]
    M2_RECON --> M2_VALIDATE_RW["Execute Rewritten Code in Sandbox"]
    M2_VALIDATE_RW --> M2_RW_PASS{"Rewritten Code\nPasses Tests?"}

    M2_RW_PASS -- No --> M2_ROLLBACK["Warning: Semantic regression detected!\nRollback to original code safely."] --> M2_SOLO_PROFILE
    M2_RW_PASS -- Yes --> M2_PAIR_POOL["Construct Comparison Pool:\n[Original, Rewritten]"] --> PROFILE_STAGE

    %% ---------------- PROFILING & TOPSIS ----------------
    PROFILE_STAGE["Multi-Metric Profiling Engine"] --> P_WARMUP["Execute W Warmup Runs (Discarded)"]
    P_WARMUP --> P_EXEC["Execute M Measurement Runs"]
    P_EXEC --> P_TIME["Record Execution Time\n(time.perf_counter_ns)"]
    P_EXEC --> P_MEM["Record Peak Memory\n(tracemalloc.get_traced_memory)"]
    P_EXEC --> P_ENG["Record Energy Footprint\n(RAPL / TDP * Delta_t)"]

    P_TIME & P_MEM & P_ENG --> P_AGG["Compute Median / Mean Values"]
    P_AGG --> TOPS_NORM["Min-Max Normalization of Metrics:\nE_norm, T_norm, M_norm in [0, 1]"]
    TOPS_NORM --> TOPS_SCORE["Compute Performance Score:\nS_i = 0.50*E_norm + 0.35*T_norm + 0.15*M_norm"]
    TOPS_SCORE --> TOPS_RANK["Sort Candidates by Ascending Score S_i"]
    TOPS_RANK --> SELECT_WINNER["Select Rank #1 as Optimal Solution\nCompute % Improvement vs Baseline/Mean"]

    SELECT_WINNER --> WRITE_OUTPUT["Generate Evaluation Report (JSON)\nSave Optimized Code (.py)\nRender Terminal Comparison Table"]
    WRITE_OUTPUT --> SUCCESS_END(["Optimal Solution Delivered"])

    %% Styling
    classDef startEnd fill:#0f2e22,stroke:#00e5a0,stroke-width:2px,color:#00e5a0;
    classDef decision fill:#112030,stroke:#00c9d4,stroke-width:1.5px,color:#e8f5f0;
    classDef process fill:#141f2d,stroke:#00c9d4,stroke-width:1.5px,color:#e8f5f0;
    classDef errNode fill:#2d1313,stroke:#ff6b6b,stroke-width:1.5px,color:#ff8888;
    classDef profNode fill:#2a2010,stroke:#ffb84d,stroke-width:1.5px,color:#ffe099;
    classDef decNode fill:#261338,stroke:#a78bfa,stroke-width:1.5px,color:#dfccf7;

    class START,SUCCESS_END startEnd;
    class CHECK_MODE,M1_PROMPT,M1_API_OK,M1_PASS,M1_NEXT,M1_CHECK_SURVIVORS,M2_INPUT,M2_ORIG_PASS,M2_PARSE_OK,M2_HAS_PATTERNS,M2_RW_PASS decision;
    class INIT,M1_LLM,M1_CLEAN,M1_LOAD_TESTS,M1_SANDBOX,M1_PASS_LOG,M2_READ,M2_VERIFY_ORIG,M2_PARSE,M2_DETECT,M2_APPLY_RULES,M2_RECON,M2_VALIDATE_RW,M2_PAIR_POOL process;
    class ERR_M1_PARAM,ERR_API,ERR_NO_VALID,ERR_M2_PARAM,ERR_ORIG_FAIL,ERR_AST,TERMINATE errNode;
    class M1_FAIL_LOG,M2_ROLLBACK,M2_NO_OP errNode;
    class PROFILE_STAGE,P_WARMUP,P_EXEC,P_TIME,P_MEM,P_ENG,P_AGG,M2_SOLO_PROFILE profNode;
    class TOPS_NORM,TOPS_SCORE,TOPS_RANK,SELECT_WINNER,WRITE_OUTPUT decNode;
```

---

## 4. Component Interaction Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Developer / Researcher
    participant CLI as CLI / Main Router
    participant M1 as Mode 1 Selector
    participant LLM as LLM API Provider
    participant AST as AST Refactoring Engine
    participant Sand as Testing Sandbox
    participant Prof as Multi-Metric Profiler
    participant TOPS as TOPSIS Decision Engine

    alt Mode 1: Generate & Select Pipeline
        User->>CLI: python -m ecocode.main --mode 1 -p "Prompt" -t tests.json
        CLI->>M1: run_mode1(prompt, test_file, num_candidates=N)
        M1->>LLM: POST /chat/completions (N candidates, temp=0.7)
        LLM-->>M1: Return N Code Variations
        loop For Each Candidate C_i
            M1->>Sand: execute(candidate_code, test_cases)
            Sand-->>M1: {is_valid: bool, passes: int/total, errors: str}
        end
        M1->>Prof: profile_valid_candidates(valid_pool)
        loop Multi-Run Profiling
            Prof->>Prof: time_profiler (perf_counter_ns)
            Prof->>Prof: memory_profiler (tracemalloc)
            Prof->>Prof: energy_profiler (RAPL / TDP model)
        end
        Prof-->>M1: Aggregated ProfileResult for each C_i
        M1->>TOPS: assign_scores_to_candidates(candidates)
        TOPS->>TOPS: Min-Max Normalization -> Apply Weights (50/35/15)
        TOPS-->>M1: Ranked Candidates + Winner Selected
        M1->>CLI: Return EvaluationReport
        CLI->>User: Display ASCII Comparison Table & Save Output Files

    else Mode 2: Analyze & Rewrite Pipeline
        User->>CLI: python -m ecocode.main --mode 2 -i source.py -t tests.json
        CLI->>Sand: execute(original_code, test_cases)
        Sand-->>CLI: Original code validation status
        CLI->>AST: parse_and_detect(original_code)
        AST-->>CLI: Detected Anti-Patterns [R001, R002, ...]
        CLI->>AST: apply_transformations(tree)
        AST-->>CLI: Rewritten Code
        CLI->>Sand: execute(rewritten_code, test_cases)
        Sand-->>CLI: Rewritten code validation status
        CLI->>Prof: profile([Original, Rewritten])
        Prof-->>CLI: Comparative Profile Data
        CLI->>TOPS: Evaluate & Select Best Version
        TOPS-->>CLI: Final Decision + Delta Metrics
        CLI->>User: Display Diff Summary & Save Refactored Code
    end
```

---

## 5. TOPSIS Decision Engine Formulation

### 5.1 Multi-Criteria Optimization Model

The EcoCode-LLM Decision Engine models candidate evaluation as a multi-criteria optimization problem where lower metric values correspond to superior candidates (cost criteria).

$$\min \quad f(C_i) = \Big( E(C_i), \; T(C_i), \; M(C_i) \Big)$$

Where:
- $E(C_i)$: Measured Energy Consumption in Joules ($\text{J}$)
- $T(C_i)$: Monotonic Execution Time in Milliseconds ($\text{ms}$)
- $M(C_i)$: Peak Resident Memory in Kilobytes ($\text{KB}$)

```mermaid
flowchart LR
    subgraph INPUT_DATA [" Raw Metric Matrix (m candidates x 3 metrics) "]
        M_RAW["Energy E_i (J)\nTime T_i (ms)\nMemory M_i (KB)"]
    end

    subgraph STEP1 [" 1. Min-Max Normalization "]
        NORM_EQ["norm_x = (x_i - min_x) / (max_x - min_x + eps)\nMaps all metrics to range [0.0, 1.0]"]
    end

    subgraph STEP2 [" 2. Weight Assignment Matrix "]
        W_E["w_Energy = 0.50 (Highest Priority)"]
        W_T["w_Time = 0.35 (Performance)"]
        W_M["w_Memory = 0.15 (Footprint)"]
    end

    subgraph STEP3 [" 3. Composite Score Formulation "]
        SCORE_EQ["S_i = (w_E * E_norm) + (w_T * T_norm) + (w_M * M_norm)\nLower Score = Closer to Ideal Solution (0, 0, 0)"]
    end

    subgraph STEP4 [" 4. Ranking & Selection "]
        WINNER["Rank #1: Minimum S_i\nCompute Energy & Speedup Gain vs Baseline"]
    end

    INPUT_DATA --> STEP1
    STEP1 --> STEP2
    STEP2 --> STEP3
    STEP3 --> STEP4

    style INPUT_DATA fill:#111827,stroke:#00c9d4,stroke-width:1.5px,color:#e8f5f0;
    style STEP1 fill:#172554,stroke:#3b82f6,stroke-width:1.5px,color:#e8f5f0;
    style STEP2 fill:#1e1b4b,stroke:#8b5cf6,stroke-width:1.5px,color:#e8f5f0;
    style STEP3 fill:#311042,stroke:#d946ef,stroke-width:1.5px,color:#e8f5f0;
    style STEP4 fill:#064e3b,stroke:#00e5a0,stroke-width:2px,color:#ffffff;
```

---

## 6. Supported AST Energy Optimization Rules (Mode 2)

| Rule ID | Anti-Pattern Name | Inefficient AST Structure | Optimized Transformation | Energy Impact |
| :--- | :--- | :--- | :--- | :--- |
| **R001** | Quadratic Nested Membership | `for x in A: if x in list_B` ($O(n \cdot m)$) | Convert target collection to `set(list_B)` prior to loop ($O(n + m)$) | **High** (Up to 90% reduction) |
| **R002** | In-Loop String Accumulation | `s = ""; for x in A: s += x` | Replace with `"".join([...])` list comprehension | **Medium-High** (Reduces memory re-allocations) |
| **R003** | Invariant Function Re-computation | `for x in A: if x > len(B): ...` | Hoist invariant expression `_len = len(B)` outside loop | **Medium** (Eliminates repeated bytecode calls) |
| **R004** | Redundant Lookup Operations | `for k in dict.keys(): v = dict[k]` | Refactor to `for k, v in dict.items():` | **Low-Medium** (Avoids hashing overhead) |
| **R005** | Naive List Deduplication | `res = []; for x in A: if x not in res: res.append(x)` | Replace with `list(dict.fromkeys(A))` or `set()` | **High** (Eliminates quadratic linear scan) |
| **R006** | Uncached Recursion | Exponential recursive function calls | Decorate with `@functools.lru_cache(maxsize=None)` | **Critical** ($O(2^n) \to O(n)$ complexity reduction) |

---

*Generated for the EcoCode-LLM Research Project &middot; UIU Green Computing.*
