import os
import sys
import json
import tempfile
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# Ensure project root is in sys.path
_PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

class EcoCodeGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("EcoCode-LLM Desktop GUI")
        self.geometry("1280x880")
        self.configure(bg="#121214") # Modern dark charcoal background
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Color palette
        self.bg_dark = "#121214"
        self.bg_card = "#1a1a1e"
        self.bg_editor = "#1e1e24"
        self.text_light = "#f3f4f6"
        self.text_muted = "#9ca3af"
        self.green_accent = "#10b981" # Modern emerald green
        self.blue_accent = "#3b82f6"
        self.border_color = "#374151"
        self.button_hover = "#059669"
        
        # Apply style modifications
        self.style.configure(".", background=self.bg_dark, foreground=self.text_light)
        self.style.configure("TFrame", background=self.bg_dark)
        self.style.configure("Card.TFrame", background=self.bg_card, relief="flat")
        self.style.configure("TLabel", background=self.bg_dark, foreground=self.text_light, font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground=self.green_accent)
        self.style.configure("Sub.TLabel", font=("Segoe UI", 9, "italic"), foreground=self.text_muted)
        self.style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"), foreground=self.green_accent)
        
        # Notebook Styling
        self.style.configure("TNotebook", background=self.bg_dark, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.bg_card, foreground=self.text_muted, padding=[20, 6], font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", self.green_accent)], foreground=[("selected", "white")])
        
        # Buttons Styling
        self.style.configure("Green.TButton", background=self.green_accent, foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0)
        self.style.map("Green.TButton", background=[("active", self.button_hover)])
        
        self.style.configure("Blue.TButton", background=self.blue_accent, foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0)
        self.style.map("Blue.TButton", background=[("active", "#2563eb")])

        self.style.configure("Gray.TButton", background=self.border_color, foreground=self.text_light, font=("Segoe UI", 9), borderwidth=0)
        self.style.map("Gray.TButton", background=[("active", "#4b5563")])

        # Entry Styling
        self.style.configure("TEntry", fieldbackground=self.bg_card, foreground="white", borderwidth=1, bordercolor=self.border_color)
        
        # Treeview Styling for Tables
        self.style.configure("Treeview", background=self.bg_card, foreground=self.text_light, fieldbackground=self.bg_card, rowheight=25, font=("Segoe UI", 9), borderwidth=0)
        self.style.configure("Treeview.Heading", background=self.border_color, foreground=self.text_light, font=("Segoe UI", 9, "bold"), borderwidth=0)
        self.style.map("Treeview", background=[("selected", self.green_accent)], foreground=[("selected", "white")])
        
        # Variables
        self.mode1_prompt = tk.StringVar(value="Write a function to find all duplicates in a list")
        self.mode1_test_file = tk.StringVar(value=str(Path(_PROJECT_ROOT) / "benchmarks" / "test_cases" / "tests_03_find_duplicates.json"))
        self.mode1_output = tk.StringVar(value=str(Path(_PROJECT_ROOT) / "outputs" / "reports" / "generation_report.json"))
        self.mode1_num_candidates = tk.StringVar(value="5")
        
        self.mode2_input_file = tk.StringVar(value=str(Path(_PROJECT_ROOT) / "benchmarks" / "problems" / "sample_unoptimized.py"))
        self.mode2_test_file = tk.StringVar(value=str(Path(_PROJECT_ROOT) / "benchmarks" / "test_cases" / "tests_03_find_duplicates.json"))
        self.mode2_output = tk.StringVar(value=str(Path(_PROJECT_ROOT) / "outputs" / "reports" / "optimization_report.json"))
        
        self.mode1_candidates = []
        self.mode2_candidates = []
        
        self.build_main_layout()

    def build_main_layout(self):
        # Master container
        self.main_container = ttk.Frame(self, padding=15)
        self.main_container.pack(fill="both", expand=True)
        
        # 1. Header Frame
        header = ttk.Frame(self.main_container)
        header.pack(fill="x", pady=(0, 10))
        
        title_lbl = ttk.Label(header, text="EcoCode-LLM Desktop GUI", style="Header.TLabel")
        title_lbl.pack(anchor="w")
        
        sub_lbl = ttk.Label(header, text="Green AI Middleware: Energy-Efficient Code Generation, AST Refactoring, & TOPSIS Decision Engine", style="Sub.TLabel")
        sub_lbl.pack(anchor="w", pady=(2, 0))
        
        # Master Vertical PanedWindow split between Notebook and Log console (for resizable split design)
        self.master_pane = ttk.PanedWindow(self.main_container, orient="vertical")
        self.master_pane.pack(fill="both", expand=True)
        
        # Top panel for the main notebook
        notebook_frame = ttk.Frame(self.master_pane)
        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill="both", expand=True)
        
        self.tab1 = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab1, text="Mode 1: Generate & Select")
        
        self.tab2 = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab2, text="Mode 2: Analyze & Rewrite")
        
        self.master_pane.add(notebook_frame, weight=3) # Takes 75% default height
        
        # Build contents inside tabs
        self.build_mode1_tab()
        self.build_mode2_tab()
        
        # Bottom panel for Log Console (Utilizing space via resizable split)
        log_frame = ttk.Frame(self.master_pane)
        
        lbl_console = ttk.Label(log_frame, text="System Execution Logs & Stdout Output (Drag boundary border above to resize log height):", font=("Segoe UI", 9, "bold"), foreground=self.text_muted)
        lbl_console.pack(anchor="w", pady=(5, 3))
        
        self.console_txt = scrolledtext.ScrolledText(log_frame, bg="#0d0d0f", fg="#10b981", font=("Consolas", 10), insertbackground="white", relief="flat")
        self.console_txt.pack(fill="both", expand=True, pady=(0, 5))
        self.console_txt.insert(tk.END, "[SYSTEM]: EcoCode GUI initialized. Ready to execute workflows.\n")
        self.console_txt.configure(state="disabled")
        
        self.master_pane.add(log_frame, weight=1) # Takes 25% default height

    # ==================== MODE 1 TAB (GENERATE & SELECT) ====================
    def build_mode1_tab(self):
        # Split Tab 1 into Left Settings and Right Results
        paned = ttk.PanedWindow(self.tab1, orient="horizontal")
        paned.pack(fill="both", expand=True)
        
        left_frame = ttk.Frame(paned, padding=(0, 0, 10, 0))
        right_frame = ttk.Frame(paned)
        
        paned.add(left_frame, weight=3)
        paned.add(right_frame, weight=7)
        
        # Left settings contents
        lbl_config = ttk.Label(left_frame, text="Generation Parameters", style="Section.TLabel")
        lbl_config.pack(anchor="w", pady=(0, 10))
        
        # Prompt Entry
        lbl_prompt = ttk.Label(left_frame, text="Problem Prompt:")
        lbl_prompt.pack(anchor="w", pady=(5, 2))
        self.m1_prompt_txt = scrolledtext.ScrolledText(left_frame, height=5, bg=self.bg_card, fg="white", font=("Segoe UI", 10), insertbackground="white", relief="flat")
        self.m1_prompt_txt.insert("1.0", self.mode1_prompt.get())
        self.m1_prompt_txt.pack(fill="x", pady=(0, 5))
        
        # Test Cases Path
        lbl_tests = ttk.Label(left_frame, text="Test File Path (JSON - Optional):")
        lbl_tests.pack(anchor="w", pady=(5, 2))
        f_tests = ttk.Frame(left_frame)
        f_tests.pack(fill="x", pady=(0, 5))
        ttk.Entry(f_tests, textvariable=self.mode1_test_file).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(f_tests, text="Browse", style="Gray.TButton", command=lambda: self.browse_file(self.mode1_test_file, [("JSON files", "*.json")])).pack(side="left", padx=(0, 2))
        ttk.Button(f_tests, text="Clear", style="Gray.TButton", command=lambda: self.mode1_test_file.set("")).pack(side="right")
        
        # Candidates count N
        lbl_cand = ttk.Label(left_frame, text="Candidates (N):")
        lbl_cand.pack(anchor="w", pady=(5, 2))
        ttk.Entry(left_frame, textvariable=self.mode1_num_candidates, width=10).pack(anchor="w", pady=(0, 5))
        
        # Output Report Path
        lbl_out = ttk.Label(left_frame, text="Output Report JSON:")
        lbl_out.pack(anchor="w", pady=(5, 2))
        f_out = ttk.Frame(left_frame)
        f_out.pack(fill="x", pady=(0, 15))
        ttk.Entry(f_out, textvariable=self.mode1_output).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(f_out, text="Browse", style="Gray.TButton", command=lambda: self.browse_save_file(self.mode1_output, [("JSON files", "*.json")])).pack(side="right")
        
        # Run Button
        self.m1_run_btn = ttk.Button(left_frame, text="Run Multi-Generation", style="Green.TButton", command=lambda: self.run_pipeline_thread(1))
        self.m1_run_btn.pack(fill="x", ipady=6, pady=(10, 0))
        
        lbl_note = ttk.Label(left_frame, text="Note: Prompted code must define the function name specified in the test JSON.", style="Sub.TLabel")
        lbl_note.pack(anchor="w", pady=(10, 0))
        
        # Right Results Panel: Vertical PanedWindow split between Code Editors and TOPSIS Table
        right_pane = ttk.PanedWindow(right_frame, orient="vertical")
        right_pane.pack(fill="both", expand=True)
        
        # Top section: selectors and editors
        editors_container = ttk.Frame(right_pane)
        
        # Selector headers
        selector_frame = ttk.Frame(editors_container)
        selector_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(selector_frame, text="Compare:").pack(side="left", padx=(0, 5))
        self.m1_dropdown_left = ttk.Combobox(selector_frame, state="readonly", width=18)
        self.m1_dropdown_left.pack(side="left", padx=(0, 15))
        self.m1_dropdown_left.bind("<<ComboboxSelected>>", self.m1_update_left_code)
        
        ttk.Label(selector_frame, text="With:").pack(side="left", padx=(0, 5))
        self.m1_dropdown_right = ttk.Combobox(selector_frame, state="readonly", width=18)
        self.m1_dropdown_right.pack(side="left")
        self.m1_dropdown_right.bind("<<ComboboxSelected>>", self.m1_update_right_code)
        
        code_split = ttk.PanedWindow(editors_container, orient="horizontal")
        code_split.pack(fill="both", expand=True, pady=(0, 5))
        
        f_left_code = ttk.Frame(code_split)
        f_right_code = ttk.Frame(code_split)
        
        code_split.add(f_left_code, weight=1)
        code_split.add(f_right_code, weight=1)
        
        self.m1_code_left = scrolledtext.ScrolledText(f_left_code, bg=self.bg_editor, fg="#e0e0e0", font=("Consolas", 10), insertbackground="white", relief="flat")
        self.m1_code_left.pack(fill="both", expand=True)
        
        self.m1_code_right = scrolledtext.ScrolledText(f_right_code, bg=self.bg_editor, fg="#e0e0e0", font=("Consolas", 10), insertbackground="white", relief="flat")
        self.m1_code_right.pack(fill="both", expand=True)
        
        right_pane.add(editors_container, weight=3) # 75% height
        
        # Bottom section: TOPSIS table
        table_frame = ttk.Frame(right_pane)
        
        lbl_tbl = ttk.Label(table_frame, text="TOPSIS Metrics Ranking Table:", font=("Segoe UI", 10, "bold"), foreground=self.green_accent)
        lbl_tbl.pack(anchor="w", pady=(5, 3))
        
        columns = ("id", "valid", "time", "memory", "energy", "topsis", "status")
        self.m1_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=5)
        self.m1_tree.pack(fill="both", expand=True)
        
        self.m1_tree.heading("id", text="Candidate ID")
        self.m1_tree.heading("valid", text="Passed Tests?")
        self.m1_tree.heading("time", text="Time (ms)")
        self.m1_tree.heading("memory", text="Memory (KB)")
        self.m1_tree.heading("energy", text="Energy (J)")
        self.m1_tree.heading("topsis", text="TOPSIS Score")
        self.m1_tree.heading("status", text="Rank Status")
        
        self.m1_tree.column("id", width=110, anchor="center")
        self.m1_tree.column("valid", width=90, anchor="center")
        self.m1_tree.column("time", width=90, anchor="center")
        self.m1_tree.column("memory", width=95, anchor="center")
        self.m1_tree.column("energy", width=95, anchor="center")
        self.m1_tree.column("topsis", width=100, anchor="center")
        self.m1_tree.column("status", width=120, anchor="center")
        
        right_pane.add(table_frame, weight=1) # 25% height

    # ==================== MODE 2 TAB (ANALYZE & REWRITE) ====================
    def build_mode2_tab(self):
        # Split Tab 2 into Left Settings and Right Comparison view
        paned = ttk.PanedWindow(self.tab2, orient="horizontal")
        paned.pack(fill="both", expand=True)
        
        left_frame = ttk.Frame(paned, padding=(0, 0, 10, 0))
        right_frame = ttk.Frame(paned)
        
        paned.add(left_frame, weight=3)
        paned.add(right_frame, weight=7)
        
        # Left Panel Configs
        lbl_config = ttk.Label(left_frame, text="Optimize Existing Code", style="Section.TLabel")
        lbl_config.pack(anchor="w", pady=(0, 10))
        
        # Input Python File Selection
        lbl_input = ttk.Label(left_frame, text="Input File (Python):")
        lbl_input.pack(anchor="w", pady=(5, 2))
        f_input = ttk.Frame(left_frame)
        f_input.pack(fill="x", pady=(0, 5))
        ttk.Entry(f_input, textvariable=self.mode2_input_file).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(f_input, text="Browse", style="Gray.TButton", command=lambda: self.load_m2_input_file()).pack(side="right")
        
        # Test Cases Path
        lbl_tests = ttk.Label(left_frame, text="Test File Path (JSON - Optional):")
        lbl_tests.pack(anchor="w", pady=(5, 2))
        f_tests = ttk.Frame(left_frame)
        f_tests.pack(fill="x", pady=(0, 5))
        ttk.Entry(f_tests, textvariable=self.mode2_test_file).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(f_tests, text="Browse", style="Gray.TButton", command=lambda: self.browse_file(self.mode2_test_file, [("JSON files", "*.json")])).pack(side="left", padx=(0, 2))
        ttk.Button(f_tests, text="Clear", style="Gray.TButton", command=lambda: self.mode2_test_file.set("")).pack(side="right")
        
        # Output Report Path
        lbl_out = ttk.Label(left_frame, text="Output Report JSON:")
        lbl_out.pack(anchor="w", pady=(5, 2))
        f_out = ttk.Frame(left_frame)
        f_out.pack(fill="x", pady=(0, 15))
        ttk.Entry(f_out, textvariable=self.mode2_output).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(f_out, text="Browse", style="Gray.TButton", command=lambda: self.browse_save_file(self.mode2_output, [("JSON files", "*.json")])).pack(side="right")
        
        # Run Button
        self.m2_run_btn = ttk.Button(left_frame, text="Optimize & Refactor", style="Green.TButton", command=lambda: self.run_pipeline_thread(2))
        self.m2_run_btn.pack(fill="x", ipady=6, pady=(10, 0))
        
        lbl_note2 = ttk.Label(left_frame, text="Note: Pasted code must contain the function expected by the selected Test File.", style="Sub.TLabel")
        lbl_note2.pack(anchor="w", pady=(10, 0))
        
        # Right Results Panel: Vertical PanedWindow split between Editors (Top) and Metrics Grid (Bottom)
        right_pane = ttk.PanedWindow(right_frame, orient="vertical")
        right_pane.pack(fill="both", expand=True)
        
        # Top section: original & rewritten code views
        editors_container = ttk.Frame(right_pane)
        
        # Side by Side Headers
        headers_frame = ttk.Frame(editors_container)
        headers_frame.pack(fill="x", pady=(0, 3))
        ttk.Label(headers_frame, text="Original Code (Paste directly or Upload file):", font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, anchor="w")
        ttk.Label(headers_frame, text="EcoCode Rewritten Output (Refactored):", font=("Segoe UI", 9, "bold"), foreground=self.green_accent).pack(side="right", expand=True, anchor="w")
        
        code_split2 = ttk.PanedWindow(editors_container, orient="horizontal")
        code_split2.pack(fill="both", expand=True, pady=(0, 5))
        
        f_m2_orig = ttk.Frame(code_split2)
        f_m2_opt = ttk.Frame(code_split2)
        
        code_split2.add(f_m2_orig, weight=1)
        code_split2.add(f_m2_opt, weight=1)
        
        self.m2_code_orig = scrolledtext.ScrolledText(f_m2_orig, bg=self.bg_editor, fg="#e0e0e0", font=("Consolas", 10), insertbackground="white", relief="flat")
        self.m2_code_orig.pack(fill="both", expand=True)
        self.init_m2_orig_code()
        
        self.m2_code_opt = scrolledtext.ScrolledText(f_m2_opt, bg=self.bg_editor, fg="#e0e0e0", font=("Consolas", 10), insertbackground="white", relief="flat")
        self.m2_code_opt.pack(fill="both", expand=True)
        
        right_pane.add(editors_container, weight=3) # 75% height
        
        # Bottom section: comparison table
        table_frame2 = ttk.Frame(right_pane)
        
        lbl_tbl2 = ttk.Label(table_frame2, text="Optimization Improvement Analysis Table:", font=("Segoe UI", 10, "bold"), foreground=self.green_accent)
        lbl_tbl2.pack(anchor="w", pady=(5, 3))
        
        columns2 = ("metric", "original", "optimized", "improvement")
        self.m2_tree = ttk.Treeview(table_frame2, columns=columns2, show="headings", height=3)
        self.m2_tree.pack(fill="both", expand=True)
        
        self.m2_tree.heading("metric", text="Evaluation Metric")
        self.m2_tree.heading("original", text="Original Code")
        self.m2_tree.heading("optimized", text="Optimized Code")
        self.m2_tree.heading("improvement", text="Resource Reduction %")
        
        self.m2_tree.column("metric", width=180, anchor="w")
        self.m2_tree.column("original", width=150, anchor="center")
        self.m2_tree.column("optimized", width=150, anchor="center")
        self.m2_tree.column("improvement", width=180, anchor="center")
        
        right_pane.add(table_frame2, weight=1) # 25% height

    # ==================== CONTROLLER FUNCTIONS ====================
    def browse_file(self, target_var, filetypes):
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            target_var.set(os.path.normpath(path))

    def browse_save_file(self, target_var, filetypes):
        path = filedialog.asksaveasfilename(filetypes=filetypes, defaultextension=filetypes[0][1][1:])
        if path:
            target_var.set(os.path.normpath(path))

    def load_m2_input_file(self):
        path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
        if path:
            self.mode2_input_file.set(os.path.normpath(path))
            try:
                content = Path(path).read_text(encoding="utf-8", errors="replace")
                self.m2_code_orig.delete("1.0", tk.END)
                self.m2_code_orig.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {e}")

    def init_m2_orig_code(self):
        path = self.mode2_input_file.get()
        if os.path.exists(path):
            try:
                content = Path(path).read_text(encoding="utf-8", errors="replace")
                self.m2_code_orig.delete("1.0", tk.END)
                self.m2_code_orig.insert(tk.END, content)
            except Exception:
                pass

    def run_pipeline_thread(self, mode):
        self.m1_run_btn.configure(state="disabled")
        self.m2_run_btn.configure(state="disabled")
        
        self.clear_console()
        self.write_console(f"[SYSTEM]: Starting execution of Mode {mode}...\n")
        
        # Delete old output report if exists to prevent loading stale cache
        out_file = self.mode1_output.get().strip() if mode == 1 else self.mode2_output.get().strip()
        if out_file and os.path.exists(out_file):
            try:
                os.remove(out_file)
            except Exception:
                pass
                
        # Build command based on mode
        cmd = [sys.executable, "-m", "ecocode.main"]
        
        temp_input_file = None
        
        if mode == 1:
            cmd.extend(["--mode", "1"])
            prompt_val = self.m1_prompt_txt.get("1.0", "end-1c").strip()
            if not prompt_val:
                messagebox.showerror("Error", "Please input a problem prompt.")
                self.reset_run_state()
                return
            cmd.extend(["--prompt", prompt_val])
            
            test_file_path = self.mode1_test_file.get().strip()
            
            import re
            stop_words = {'to', 'that', 'which', 'a', 'an', 'the', 'named', 'called', 'for', 'in', 'and', 'with', 'by', 'is', 'how', 'when', 'all'}
            prompt_func = None
            explicit_match = re.search(r'\b([a-zA-Z_]\w*)\s*\(', prompt_val)
            if explicit_match and explicit_match.group(1).lower() not in ('range', 'print', 'len', 'int', 'str', 'float', 'list', 'dict', 'set', 'def', 'if', 'for', 'while', 'return'):
                prompt_func = explicit_match.group(1)
            else:
                named_match = re.search(r'(?:function|def)\s+(?:named\s+|called\s+)?([a-zA-Z_]\w*)', prompt_val, re.IGNORECASE)
                if named_match and named_match.group(1).lower() not in stop_words:
                    prompt_func = named_match.group(1)
            
            test_func_name = None
            if test_file_path and os.path.exists(test_file_path):
                try:
                    with open(test_file_path, "r", encoding="utf-8", errors="replace") as f:
                        test_data = json.load(f)
                        test_func_name = test_data.get("function_name")
                except Exception:
                    pass
            
            # Auto-generate mock test file if no test file selected OR prompt function name doesn't match
            if not test_file_path or not os.path.exists(test_file_path) or (prompt_func and test_func_name and prompt_func != test_func_name):
                target_func = prompt_func or test_func_name or "solution"
                self.write_console(f"[SYSTEM INFO]: Auto-generating smoke-test file for target function '{target_func}'...\n")
                
                mock_json = {
                    "function_name": target_func,
                    "test_cases": [
                        {
                            "input": {},
                            "expected_output": "__ANY__"
                        }
                    ]
                }
                temp_dir = Path(_PROJECT_ROOT) / "outputs" / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                mock_test_file = temp_dir / "mode1_mock_test.json"
                mock_test_file.write_text(json.dumps(mock_json, indent=2), encoding="utf-8")
                test_file_path = str(mock_test_file)
                
            cmd.extend(["--test-file", test_file_path])
                
            if self.mode1_output.get().strip():
                cmd.extend(["--output", self.mode1_output.get().strip()])
                
            if self.mode1_num_candidates.get().strip():
                cmd.extend(["--num-candidates", self.mode1_num_candidates.get().strip()])
        else:
            cmd.extend(["--mode", "2"])
            
            # Allow user to paste code directly. If pasted, we write to a temp file and optimize that.
            code_content = self.m2_code_orig.get("1.0", "end-1c").strip()
            if not code_content:
                messagebox.showerror("Error", "Original code editor is empty. Paste code or browse a file.")
                self.reset_run_state()
                return
            
            import ast
            # Parse code and detect functions
            try:
                tree = ast.parse(code_content)
                functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
            except Exception as e:
                messagebox.showerror("Error", f"Failed to parse pasted code: {e}")
                self.reset_run_state()
                return
            
            # Determine function name from test file if selected
            test_file_path = self.mode2_test_file.get().strip()
            test_func_name = None
            if test_file_path and os.path.exists(test_file_path):
                try:
                    with open(test_file_path, "r", encoding="utf-8", errors="replace") as f:
                        test_data = json.load(f)
                        test_func_name = test_data.get("function_name")
                except Exception:
                    pass
            
            final_code = code_content
            final_test_file = test_file_path
            
            # Check if we need to auto-generate a mock test file
            # Scenario A: No functions in code -> Wrap in main_function
            if not functions:
                self.write_console("[SYSTEM INFO]: No function definitions found in code. Wrapping entire script into 'main_function'...\n")
                # Wrap code in main_function
                indented = "\n".join("    " + line for line in code_content.splitlines())
                final_code = f"def main_function():\n{indented}\n"
                
                # Create mock test file
                mock_json = {
                    "function_name": "main_function",
                    "test_cases": [
                        {
                            "input": {},
                            "expected_output": "__ANY__"
                        }
                    ]
                }
                
                temp_dir = Path(_PROJECT_ROOT) / "outputs" / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                mock_test_file = temp_dir / "mock_test_cases.json"
                mock_test_file.write_text(json.dumps(mock_json, indent=2), encoding="utf-8")
                final_test_file = str(mock_test_file)
                
            # Scenario B: Functions exist, but either no test file is selected OR the test file function name is not in the code
            elif not test_func_name or test_func_name not in functions:
                func_name = functions[0] # Take the first function defined
                self.write_console(f"[SYSTEM INFO]: Selected test file function '{test_func_name}' not found in code. Auto-generating a mock smoke-test file for function '{func_name}'...\n")
                
                # Guess arguments for this function
                first_func_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == func_name)
                args = {}
                for arg in first_func_node.args.args:
                    arg_name = arg.arg
                    if arg_name in ("self", "cls"):
                        continue
                    # Guess some dummy/mock inputs based on argument name
                    if any(x in arg_name.lower() for x in ("num", "n", "limit", "max", "width", "height", "w", "h", "iter", "len", "size", "val", "x", "y")):
                        args[arg_name] = 5
                    elif any(x in arg_name.lower() for x in ("list", "array", "arr", "lst", "nums", "elements", "data")):
                        args[arg_name] = [1, 2, 3]
                    else:
                        args[arg_name] = 1
                
                mock_json = {
                    "function_name": func_name,
                    "test_cases": [
                        {
                            "input": args,
                            "expected_output": "__ANY__"
                        }
                    ]
                }
                
                temp_dir = Path(_PROJECT_ROOT) / "outputs" / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                mock_test_file = temp_dir / "mock_test_cases.json"
                mock_test_file.write_text(json.dumps(mock_json, indent=2), encoding="utf-8")
                final_test_file = str(mock_test_file)
                
            # Prepare code execution path
            try:
                temp_dir = Path(_PROJECT_ROOT) / "outputs" / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_file = temp_dir / "direct_input.py"
                temp_file.write_text(final_code, encoding="utf-8")
                temp_input_file = str(temp_file)
                cmd.extend(["--input-file", temp_input_file])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to prepare input code: {e}")
                self.reset_run_state()
                return
            
            cmd.extend(["--test-file", final_test_file])
                
            if self.mode2_output.get().strip():
                cmd.extend(["--output", self.mode2_output.get().strip()])
        
        self.write_console(f"[RUNNING COMMAND]: {' '.join(cmd)}\n\n")
        
        threading.Thread(
            target=self.run_subprocess,
            args=(cmd, mode, temp_input_file),
            daemon=True
        ).start()

    def run_subprocess(self, cmd, mode, temp_input_file=None):
        try:
            process = subprocess.Popen(
                cmd,
                cwd=_PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace"
            )
            
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                self.write_console(line)
                
            process.wait()
            
            # Clean up temp file
            if temp_input_file and os.path.exists(temp_input_file):
                try:
                    os.remove(temp_input_file)
                except Exception:
                    pass
            
            # Process results only if command completed successfully (returncode == 0)
            if process.returncode == 0:
                if mode == 1:
                    self.load_mode1_results()
                else:
                    self.load_mode2_results()
            else:
                self.clear_results(mode)
                self.write_console(f"\n[SYSTEM]: Run completed with code {process.returncode} (Failed / Invalid candidate correctness).\n")
                
        except Exception as e:
            self.write_console(f"\n[ERROR OCCURRED]: {str(e)}\n")
            
        finally:
            self.reset_run_state()

    def reset_run_state(self):
        self.m1_run_btn.configure(state="normal")
        self.m2_run_btn.configure(state="normal")

    def clear_console(self):
        self.console_txt.configure(state="normal")
        self.console_txt.delete("1.0", tk.END)
        self.console_txt.configure(state="disabled")

    def write_console(self, text):
        self.console_txt.configure(state="normal")
        self.console_txt.insert(tk.END, text)
        self.console_txt.see(tk.END)
        self.console_txt.configure(state="disabled")

    def clear_results(self, mode):
        if mode == 1:
            self.m1_dropdown_left.set("")
            self.m1_dropdown_right.set("")
            self.m1_code_left.delete("1.0", tk.END)
            self.m1_code_right.delete("1.0", tk.END)
            for row in self.m1_tree.get_children():
                self.m1_tree.delete(row)
        else:
            self.m2_code_opt.delete("1.0", tk.END)
            for row in self.m2_tree.get_children():
                self.m2_tree.delete(row)

    # ==================== PARSE & LOAD RESULTS ====================
    def load_mode1_results(self):
        report_path = self.mode1_output.get().strip()
        if not os.path.exists(report_path):
            self.write_console("\n[WARNING]: Generation output report not found. The run might have failed to produce valid candidates.\n")
            return
            
        try:
            with open(report_path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
                
            self.mode1_candidates = data.get("candidates", [])
            winner = data.get("winner", None)
            winner_id = winner.get("id") if winner else None
            
            # Clear dropdowns & table
            self.m1_dropdown_left.set("")
            self.m1_dropdown_right.set("")
            self.m1_code_left.delete("1.0", tk.END)
            self.m1_code_right.delete("1.0", tk.END)
            for row in self.m1_tree.get_children():
                self.m1_tree.delete(row)
                
            # Populate dropdown list
            ids = [c["id"] for c in self.mode1_candidates]
            self.m1_dropdown_left["values"] = ids
            self.m1_dropdown_right["values"] = ids
            
            if ids:
                left_id = winner_id if (winner_id and winner_id in ids) else ids[0]
                self.m1_dropdown_left.set(left_id)
                self.m1_update_left_code(None)
                
                other_ids = [i for i in ids if i != left_id]
                right_id = other_ids[0] if other_ids else left_id
                self.m1_dropdown_right.set(right_id)
                self.m1_update_right_code(None)
                
            # Populate metrics table
            for c in self.mode1_candidates:
                c_id = c.get("id")
                valid = "Yes" if c.get("is_valid") else "No"
                profile = c.get("profile") or {}
                time = f"{profile.get('execution_time_ms', 'N/A')}"
                mem = f"{profile.get('peak_memory_kb', 'N/A')}"
                energy = f"{profile.get('energy_joules', 'N/A')}"
                topsis = f"{c.get('topsis_score')}" if c.get("topsis_score") is not None else "N/A"
                
                status = "Valid Candidate"
                if c_id == winner_id:
                    status = "Winner (Optimal)"
                elif not c.get("is_valid"):
                    status = "Failed Correctness Tests"
                    
                self.m1_tree.insert("", "end", values=(c_id, valid, time, mem, energy, topsis, status))
                
        except Exception as e:
            self.write_console(f"\n[ERROR PARSING M1 RESULTS]: {e}\n")

    def load_mode2_results(self):
        report_path = self.mode2_output.get().strip()
        if not os.path.exists(report_path):
            self.write_console("\n[WARNING]: Optimization report not found.\n")
            return
            
        try:
            with open(report_path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
                
            self.mode2_candidates = data.get("candidates", [])
            winner = data.get("winner", {})
            improvement_pct = data.get("improvement_pct", {})
            
            # Clear editors & grid
            self.m2_code_opt.delete("1.0", tk.END)
            for row in self.m2_tree.get_children():
                self.m2_tree.delete(row)
                
            # Display optimized code
            optimized_code = winner.get("source_code", "")
            self.m2_code_opt.insert(tk.END, optimized_code)
            
            # Populate comparison grid
            orig_c = next((c for c in self.mode2_candidates if c.get("id") in ("Original", "C01", "C1")), None)
            opt_c = next((c for c in self.mode2_candidates if c.get("id") == "Rewritten"), None)
            
            if not opt_c:
                self.write_console("\n[INFO]: AST Analysis complete — Code contains no anti-patterns and is already optimal.\n")
                if not optimized_code and orig_c:
                    optimized_code = orig_c.get("source_code", "")
                    self.m2_code_opt.insert(tk.END, "# [INFO]: Code is already efficient. No anti-patterns detected.\n\n" + optimized_code)
                    
                orig_profile = (orig_c.get("profile") if orig_c else {}) or (winner.get("profile") if winner else {}) or {}
                time_val = f"{orig_profile.get('execution_time_ms', 'N/A')} ms"
                mem_val = f"{orig_profile.get('peak_memory_kb', 'N/A')} KB"
                energy_val = f"{orig_profile.get('energy_joules', 'N/A')} J"
                
                self.m2_tree.insert("", "end", values=("Execution Time (Speed)", time_val, time_val, "0.0% (Baseline)"))
                self.m2_tree.insert("", "end", values=("Peak Memory Usage", mem_val, mem_val, "0.0% (Baseline)"))
                self.m2_tree.insert("", "end", values=("Energy Consumption", energy_val, energy_val, "0.0% (Baseline)"))
                return
                
            orig_profile = orig_c.get("profile") or {}
            opt_profile = opt_c.get("profile") or {}
            
            time_orig = f"{orig_profile.get('execution_time_ms', 'N/A')} ms"
            time_opt = f"{opt_profile.get('execution_time_ms', 'N/A')} ms"
            time_imp = f"{improvement_pct.get('time', 0.0)}%"
            
            mem_orig = f"{orig_profile.get('peak_memory_kb', 'N/A')} KB"
            mem_opt = f"{opt_profile.get('peak_memory_kb', 'N/A')} KB"
            mem_imp = f"{improvement_pct.get('memory', 0.0)}%"
            
            energy_orig = f"{orig_profile.get('energy_joules', 'N/A')} J"
            energy_opt = f"{opt_profile.get('energy_joules', 'N/A')} J"
            energy_imp = f"{improvement_pct.get('energy', 0.0)}%"
            
            self.m2_tree.insert("", "end", values=("Execution Time (Speed)", time_orig, time_opt, time_imp))
            self.m2_tree.insert("", "end", values=("Peak Memory Usage", mem_orig, mem_opt, mem_imp))
            self.m2_tree.insert("", "end", values=("Energy Consumption", energy_orig, energy_opt, energy_imp))
            
        except Exception as e:
            self.write_console(f"\n[ERROR PARSING M2 RESULTS]: {e}\n")

    def m1_update_left_code(self, event):
        sel_id = self.m1_dropdown_left.get()
        cand = next((c for c in self.mode1_candidates if c.get("id") == sel_id), None)
        self.m1_code_left.delete("1.0", tk.END)
        if cand:
            code = cand.get("source_code", "")
            if not cand.get("is_valid"):
                code = f"# [STATUS: FAILED CORRECTNESS TESTS]\n# Raw output returned by candidate {sel_id}:\n\n" + code
            self.m1_code_left.insert(tk.END, code)

    def m1_update_right_code(self, event):
        sel_id = self.m1_dropdown_right.get()
        cand = next((c for c in self.mode1_candidates if c.get("id") == sel_id), None)
        self.m1_code_right.delete("1.0", tk.END)
        if cand:
            code = cand.get("source_code", "")
            if not cand.get("is_valid"):
                code = f"# [STATUS: FAILED CORRECTNESS TESTS]\n# Raw output returned by candidate {sel_id}:\n\n" + code
            self.m1_code_right.insert(tk.END, code)

if __name__ == "__main__":
    app = EcoCodeGUI()
    app.mainloop()
