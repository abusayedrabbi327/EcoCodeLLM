import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
TEMP_DIR = ROOT / "outputs" / "temp"
DEFAULT_TESTS = ROOT / "benchmarks" / "test_cases" / "tests_03_find_duplicates.json"
DEFAULT_INPUT = ROOT / "benchmarks" / "problems" / "sample_unoptimized.py"

st.set_page_config(
    page_title="EcoCode Studio",
    page_icon="E",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
    :root { --ink:#17221d; --muted:#66736c; --line:#dfe8e1; --paper:#f6f8f5; --panel:#ffffff; --green:#176b4d; --mint:#dff1e7; --orange:#c86b32; }
    .stApp { background:var(--paper); color:var(--ink); font-family:'Manrope', sans-serif; }
    [data-testid='stSidebar'] { background:#173a2b; border-right:0; }
    [data-testid='stSidebar'] * { color:#eef8f1 !important; }
    [data-testid='stSidebar'] .stRadio label { padding:0.55rem 0.7rem; border-radius:8px; }
    [data-testid='stSidebar'] .stRadio label:hover { background:rgba(255,255,255,.09); }
    h1, h2, h3 { font-family:'Manrope', sans-serif; letter-spacing:0; color:var(--ink); }
    h1 { font-size:2.15rem; font-weight:800; margin-bottom:0.2rem; }
    h2 { font-size:1.25rem; font-weight:800; }
    .eyebrow { color:var(--green); font-size:.73rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.35rem; }
    .hero { border-bottom:1px solid var(--line); padding:1.2rem 0 1.25rem; margin-bottom:1.5rem; }
    .hero-copy { color:var(--muted); max-width:760px; font-size:.97rem; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:1.15rem 1.25rem; box-shadow:0 8px 24px rgba(25,55,38,.04); }
    .panel-title { font-size:1.03rem; font-weight:800; margin-bottom:.2rem; }
    .panel-caption { color:var(--muted); font-size:.82rem; margin-bottom:1rem; }
    .metric { background:#edf6ef; border-left:3px solid var(--green); border-radius:7px; padding:.8rem .9rem; min-height:78px; }
    .metric-label { color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; font-weight:700; }
    .metric-value { color:var(--ink); font-size:1.22rem; font-weight:800; margin-top:.22rem; }
    .status { display:inline-block; padding:.27rem .55rem; border-radius:5px; background:var(--mint); color:var(--green); font-size:.75rem; font-weight:800; }
    .hint { color:var(--muted); font-size:.78rem; line-height:1.45; }
    .stButton > button { border-radius:7px; border:0; background:var(--green); color:white; font-weight:800; min-height:2.65rem; }
    .stButton > button:hover { background:#0f5039; color:white; }
    .stTextInput input, .stTextArea textarea { border-radius:7px; border:1px solid var(--line); }
    code, pre { font-family:'DM Mono', monospace !important; }
    [data-testid='stMetric'] { background:#edf6ef; border:1px solid #d6e9da; padding:.7rem; border-radius:7px; }
    footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def persist_upload(uploaded_file, label: str) -> Path | None:
    if uploaded_file is None:
        return None
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    payload = uploaded_file.getvalue()
    digest = hashlib.sha256(payload).hexdigest()[:12]
    destination = TEMP_DIR / f"{label}_{digest}_{Path(uploaded_file.name).name}"
    destination.write_bytes(payload)
    return destination


def run_cli(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ecocode.main", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def show_report(report_path: Path, optimized_path: Path | None = None) -> None:
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            winner = report.get("winner") or {}
            profile = winner.get("profile") or {}
            cols = st.columns(4)
            values = [
                ("Winner", winner.get("id", "Not selected")),
                ("Valid candidates", f"{report.get('valid_candidates', 0)} / {report.get('total_candidates', 0)}"),
                ("Execution time", f"{profile.get('execution_time_ms', 'N/A')} ms"),
                ("Estimated energy", f"{profile.get('energy_joules', 'N/A')} J"),
            ]
            for column, (label, value) in zip(cols, values):
                column.markdown(f"<div class='metric'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>", unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            with st.expander("Evaluation report", expanded=False):
                st.json(report)
            if optimized_path and optimized_path.exists():
                with st.expander("Selected source code", expanded=True):
                    st.code(optimized_path.read_text(encoding="utf-8"), language="python")
        except (OSError, json.JSONDecodeError) as error:
            st.warning(f"The report could not be read: {error}")
    else:
        st.info("The workflow completed without creating a report at the selected path.")


def run_mode2() -> None:
    st.markdown("<div class='panel-title'>Analyze and rewrite</div><div class='panel-caption'>Validate an existing Python program, apply AST refactoring rules, then compare resource usage.</div>", unsafe_allow_html=True)
    left, right = st.columns([1, 1.45], gap="large")
    with left:
        uploaded_source = st.file_uploader("Python source", type=["py"], key="m2_source")
        uploaded_tests = st.file_uploader("Test cases", type=["json"], key="m2_tests")
        source_path = st.text_input("Input file path", str(DEFAULT_INPUT), key="m2_source_path")
        test_path = st.text_input("Test file path", str(DEFAULT_TESTS), key="m2_test_path")
        output_path = st.text_input("Report path", str(ROOT / "outputs" / "reports" / "optimization_report.json"), key="m2_output")
        st.markdown("<div class='hint'>The original implementation must pass its tests before EcoCode will compare a rewrite.</div>", unsafe_allow_html=True)
        run = st.button("Run analysis", type="primary", use_container_width=True, key="m2_run")
    with right:
        st.markdown("<div class='panel-title'>Workflow result</div><div class='panel-caption'>The result panel keeps the evidence close to the action that produced it.</div>", unsafe_allow_html=True)
        if run:
            source = persist_upload(uploaded_source, "source")
            tests = persist_upload(uploaded_tests, "tests")
            input_file = source or resolve_path(source_path)
            test_file = tests or resolve_path(test_path)
            report_file = resolve_path(output_path)
            with st.spinner("Analyzing and validating the rewrite..."):
                result = run_cli(["--mode", "2", "--input-file", str(input_file), "--test-file", str(test_file), "--output", str(report_file)])
            if result.returncode == 0:
                st.markdown("<span class='status'>Completed successfully</span>", unsafe_allow_html=True)
                show_report(report_file, ROOT / "outputs" / "rewritten_code" / "optimized_code.py")
            else:
                st.error("The analysis did not complete successfully.")
            with st.expander("Execution log", expanded=result.returncode != 0):
                st.code((result.stdout or "") + ("\n" + result.stderr if result.stderr else ""), language="text")
        else:
            st.markdown("<div class='hint'>Run a workflow to see validation status, selected code, and measured metrics here.</div>", unsafe_allow_html=True)


def run_mode1() -> None:
    st.markdown("<div class='panel-title'>Generate and select</div><div class='panel-caption'>Ask an LLM for several implementations, validate them, and rank the valid candidates by resource cost.</div>", unsafe_allow_html=True)
    left, right = st.columns([1, 1.45], gap="large")
    with left:
        prompt = st.text_area("Problem prompt", "Write a function to find all duplicates in a list", height=145, key="m1_prompt")
        uploaded_tests = st.file_uploader("Test cases", type=["json"], key="m1_tests")
        test_path = st.text_input("Test file path", str(DEFAULT_TESTS), key="m1_test_path")
        output_path = st.text_input("Report path", str(ROOT / "outputs" / "reports" / "generation_report.json"), key="m1_output")
        candidate_count = st.number_input("Candidates to generate", min_value=1, max_value=10, value=3, step=1, key="m1_count")
        api_ready = bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
        st.markdown(f"<div class='hint'>{'Provider key detected.' if api_ready else 'Configure OPENAI_API_KEY or OPENROUTER_API_KEY before running generation.'}</div>", unsafe_allow_html=True)
        run = st.button("Generate candidates", type="primary", use_container_width=True, key="m1_run")
    with right:
        st.markdown("<div class='panel-title'>Selection result</div><div class='panel-caption'>TOPSIS prioritizes energy, then execution time, then memory using the configured weights.</div>", unsafe_allow_html=True)
        if run:
            tests = persist_upload(uploaded_tests, "tests") or resolve_path(test_path)
            report_file = resolve_path(output_path)
            with st.spinner("Generating, testing, and profiling candidates..."):
                result = run_cli(["--mode", "1", "--prompt", prompt, "--test-file", str(tests), "--output", str(report_file), "--num-candidates", str(candidate_count)])
            if result.returncode == 0:
                st.markdown("<span class='status'>Completed successfully</span>", unsafe_allow_html=True)
                show_report(report_file)
            else:
                st.error("Candidate generation did not complete successfully.")
            with st.expander("Execution log", expanded=result.returncode != 0):
                st.code((result.stdout or "") + ("\n" + result.stderr if result.stderr else ""), language="text")
        else:
            st.markdown("<div class='hint'>Run a workflow to see candidate validity, profiling data, and the selected winner here.</div>", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("<div style='font-size:1.3rem;font-weight:800;'>EcoCode Studio</div><div style='opacity:.72;font-size:.78rem;margin-top:.25rem;'>Resource-aware Python workflows</div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:rgba(255,255,255,.18);margin:1.3rem 0;'>", unsafe_allow_html=True)
    mode = st.radio("WORKFLOW", ["Analyze and rewrite", "Generate and select"], label_visibility="visible")
    st.markdown("<div style='position:fixed;bottom:1.4rem;font-size:.74rem;opacity:.65;'>EcoCode-LLM / local workspace</div>", unsafe_allow_html=True)

st.markdown("<div class='hero'><div class='eyebrow'>EcoCode / resource-aware engineering</div><h1>Make Python work lighter.</h1><div class='hero-copy'>Validate behavior first, then use measurable execution signals to guide a cleaner implementation.</div></div>", unsafe_allow_html=True)

if mode == "Analyze and rewrite":
    run_mode2()
else:
    run_mode1()
