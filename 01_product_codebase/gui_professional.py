import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

ROOT = Path(__file__).resolve().parent
DEFAULT_TESTS = ROOT / "benchmarks" / "test_cases" / "tests_03_find_duplicates.json"
DEFAULT_INPUT = ROOT / "benchmarks" / "problems" / "sample_unoptimized.py"


class EcoCodeStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EcoCode Studio")
        self.geometry("1360x900")
        self.minsize(1050, 720)
        self.configure(bg="#f5f7f4")

        self.colors = {
            "ink": "#17221d",
            "muted": "#69766e",
            "line": "#d8e2da",
            "paper": "#f5f7f4",
            "panel": "#ffffff",
            "green": "#176b4d",
            "green_dark": "#0f5039",
            "mint": "#e4f2e8",
            "editor": "#16211c",
            "editor_text": "#e5f2e8",
            "orange": "#c86b32",
        }
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.configure_styles()

        self.events = queue.Queue()
        self.running = False
        self.mode1_prompt = tk.StringVar(value="Write a function to find all duplicates in a list")
        self.mode1_tests = tk.StringVar(value=str(DEFAULT_TESTS))
        self.mode1_output = tk.StringVar(value=str(ROOT / "outputs" / "reports" / "generation_report.json"))
        self.mode1_count = tk.StringVar(value="3")
        self.mode2_input = tk.StringVar(value=str(DEFAULT_INPUT))
        self.mode2_tests = tk.StringVar(value=str(DEFAULT_TESTS))
        self.mode2_output = tk.StringVar(value=str(ROOT / "outputs" / "reports" / "optimization_report.json"))

        self.build_layout()
        self.after(100, self.process_events)
        self.load_original_source()

    def configure_styles(self):
        self.style.configure("TFrame", background=self.colors["paper"])
        self.style.configure("Panel.TFrame", background=self.colors["panel"])
        self.style.configure("TLabel", background=self.colors["paper"], foreground=self.colors["ink"], font=("Segoe UI", 10))
        self.style.configure("Muted.TLabel", background=self.colors["paper"], foreground=self.colors["muted"], font=("Segoe UI", 9))
        self.style.configure("Title.TLabel", background=self.colors["paper"], foreground=self.colors["ink"], font=("Segoe UI", 24, "bold"))
        self.style.configure("Eyebrow.TLabel", background=self.colors["paper"], foreground=self.colors["green"], font=("Segoe UI", 9, "bold"))
        self.style.configure("PanelTitle.TLabel", background=self.colors["panel"], foreground=self.colors["ink"], font=("Segoe UI", 12, "bold"))
        self.style.configure("PanelMuted.TLabel", background=self.colors["panel"], foreground=self.colors["muted"], font=("Segoe UI", 9))
        self.style.configure("Primary.TButton", background=self.colors["green"], foreground="white", borderwidth=0, padding=(14, 9), font=("Segoe UI", 10, "bold"))
        self.style.map("Primary.TButton", background=[("active", self.colors["green_dark"])])
        self.style.configure("Quiet.TButton", background="#edf2ee", foreground=self.colors["ink"], borderwidth=0, padding=(9, 7), font=("Segoe UI", 9, "bold"))
        self.style.map("Quiet.TButton", background=[("active", "#dfe9e1")])
        self.style.configure("TNotebook", background=self.colors["paper"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#e7eee8", foreground=self.colors["muted"], padding=(18, 9), font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", self.colors["green"])], foreground=[("selected", "white")])
        self.style.configure("Treeview", background=self.colors["panel"], fieldbackground=self.colors["panel"], foreground=self.colors["ink"], rowheight=28, borderwidth=0, font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", background="#e8f0e9", foreground=self.colors["ink"], font=("Segoe UI", 9, "bold"), borderwidth=0)
        self.style.map("Treeview", background=[("selected", self.colors["mint"])], foreground=[("selected", self.colors["ink"])])
        self.style.configure("TEntry", fieldbackground="white", foreground=self.colors["ink"], bordercolor=self.colors["line"], padding=7)

    def build_layout(self):
        shell = ttk.Frame(self, padding=(28, 22, 28, 18))
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="ECOCODE / RESOURCE-AWARE ENGINEERING", style="Eyebrow.TLabel").pack(anchor="w")
        ttk.Label(shell, text="Make Python work lighter.", style="Title.TLabel").pack(anchor="w", pady=(3, 1))
        ttk.Label(shell, text="Validate behavior first, then compare execution signals across clean implementations.", style="Muted.TLabel").pack(anchor="w", pady=(0, 18))

        notebook = ttk.Notebook(shell)
        notebook.pack(fill="both", expand=True)
        self.mode1_tab = ttk.Frame(notebook, padding=15)
        self.mode2_tab = ttk.Frame(notebook, padding=15)
        notebook.add(self.mode2_tab, text="  Analyze and rewrite  ")
        notebook.add(self.mode1_tab, text="  Generate and select  ")
        self.build_mode1()
        self.build_mode2()

        log_panel = ttk.Frame(shell, style="Panel.TFrame", padding=12)
        log_panel.pack(fill="x", pady=(14, 0))
        header = ttk.Frame(log_panel, style="Panel.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="Execution log", style="PanelTitle.TLabel").pack(side="left")
        ttk.Button(header, text="Clear", style="Quiet.TButton", command=self.clear_log).pack(side="right")
        self.log = scrolledtext.ScrolledText(log_panel, height=6, bg=self.colors["editor"], fg=self.colors["editor_text"], insertbackground="white", relief="flat", font=("Consolas", 9), padx=10, pady=8)
        self.log.pack(fill="x", pady=(9, 0))
        self.log.configure(state="disabled")
        self.write_log("Ready. Choose a workflow and run an analysis.")

    def field(self, parent, label, variable, browse_command=None):
        ttk.Label(parent, text=label, style="PanelMuted.TLabel").pack(anchor="w", pady=(8, 4))
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x")
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True)
        if browse_command:
            ttk.Button(row, text="Browse", style="Quiet.TButton", command=browse_command).pack(side="left", padx=(7, 0))

    def build_mode1(self):
        left, right = self.make_columns(self.mode1_tab)
        ttk.Label(left, text="Generate and select", style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(left, text="Generate several implementations, test them, and rank only valid candidates.", style="PanelMuted.TLabel", wraplength=350).pack(anchor="w", pady=(3, 10))
        ttk.Label(left, text="Problem prompt", style="PanelMuted.TLabel").pack(anchor="w", pady=(5, 4))
        self.prompt_text = tk.Text(left, height=6, wrap="word", bg="white", fg=self.colors["ink"], relief="solid", borderwidth=1, highlightthickness=0, font=("Segoe UI", 10), padx=8, pady=8)
        self.prompt_text.insert("1.0", self.mode1_prompt.get())
        self.prompt_text.pack(fill="x")
        self.field(left, "Test cases JSON", self.mode1_tests, lambda: self.choose_file(self.mode1_tests, [("JSON files", "*.json")]))
        self.field(left, "Report output", self.mode1_output, lambda: self.choose_save(self.mode1_output))
        self.field(left, "Candidates to generate", self.mode1_count)
        ttk.Label(left, text="Energy 50%  /  time 35%  /  memory 15%", style="Muted.TLabel").pack(anchor="w", pady=(10, 15))
        self.mode1_button = ttk.Button(left, text="Generate candidates", style="Primary.TButton", command=lambda: self.start_workflow(1))
        self.mode1_button.pack(fill="x")

        ttk.Label(right, text="Selection result", style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(right, text="The selected candidate and measurements appear here after a run.", style="PanelMuted.TLabel").pack(anchor="w", pady=(3, 10))
        self.mode1_summary = ttk.Label(right, text="No run yet", style="PanelMuted.TLabel")
        self.mode1_summary.pack(anchor="w", pady=(0, 8))
        self.mode1_code = self.make_editor(right, "Selected source code")
        self.mode1_tree = self.make_tree(right, ("id", "valid", "time", "memory", "energy", "score"), ("Candidate", "Valid", "Time (ms)", "Memory (KB)", "Energy (J)", "TOPSIS"))

    def build_mode2(self):
        left, right = self.make_columns(self.mode2_tab)
        ttk.Label(left, text="Analyze and rewrite", style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(left, text="Apply AST-based refactoring rules only after the original code passes its tests.", style="PanelMuted.TLabel", wraplength=350).pack(anchor="w", pady=(3, 10))
        self.field(left, "Input Python file", self.mode2_input, self.choose_input)
        self.field(left, "Test cases JSON", self.mode2_tests, lambda: self.choose_file(self.mode2_tests, [("JSON files", "*.json")]))
        self.field(left, "Report output", self.mode2_output, lambda: self.choose_save(self.mode2_output))
        ttk.Label(left, text="Original source", style="PanelMuted.TLabel").pack(anchor="w", pady=(10, 4))
        self.original_text = tk.Text(left, height=15, wrap="none", bg="white", fg=self.colors["ink"], relief="solid", borderwidth=1, highlightthickness=0, font=("Consolas", 9), padx=8, pady=8)
        self.original_text.pack(fill="both", expand=True)
        ttk.Button(left, text="Run analysis", style="Primary.TButton", command=lambda: self.start_workflow(2)).pack(fill="x", pady=(12, 0))

        ttk.Label(right, text="Optimization result", style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(right, text="Compare the rewritten source with the original measurements.", style="PanelMuted.TLabel").pack(anchor="w", pady=(3, 10))
        self.mode2_summary = ttk.Label(right, text="No run yet", style="PanelMuted.TLabel")
        self.mode2_summary.pack(anchor="w", pady=(0, 8))
        self.optimized_text = self.make_editor(right, "EcoCode rewritten source")
        self.mode2_tree = self.make_tree(right, ("metric", "original", "optimized", "change"), ("Metric", "Original", "Optimized", "Change"))

    def make_columns(self, parent):
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)
        left = ttk.Frame(container, style="Panel.TFrame", padding=16)
        right = ttk.Frame(container, style="Panel.TFrame", padding=16)
        left.pack(side="left", fill="both", expand=False, ipadx=8)
        right.pack(side="left", fill="both", expand=True, padx=(14, 0))
        container.columnconfigure(1, weight=1)
        left.configure(width=380)
        return left, right

    def make_editor(self, parent, title):
        ttk.Label(parent, text=title, style="PanelMuted.TLabel").pack(anchor="w", pady=(0, 4))
        editor = scrolledtext.ScrolledText(parent, height=15, wrap="none", bg=self.colors["editor"], fg=self.colors["editor_text"], insertbackground="white", relief="flat", font=("Consolas", 9), padx=10, pady=10)
        editor.pack(fill="both", expand=True, pady=(0, 12))
        return editor

    def make_tree(self, parent, columns, headings):
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=4)
        for column, heading in zip(columns, headings):
            tree.heading(column, text=heading)
            tree.column(column, width=110, anchor="center")
        tree.pack(fill="x")
        return tree

    def choose_file(self, variable, types):
        path = filedialog.askopenfilename(filetypes=types)
        if path:
            variable.set(os.path.normpath(path))

    def choose_save(self, variable):
        path = filedialog.asksaveasfilename(filetypes=[("JSON files", "*.json")], defaultextension=".json")
        if path:
            variable.set(os.path.normpath(path))

    def choose_input(self):
        self.choose_file(self.mode2_input, [("Python files", "*.py")])
        self.load_original_source()

    def load_original_source(self):
        path = Path(self.mode2_input.get())
        if path.exists() and hasattr(self, "original_text"):
            self.original_text.delete("1.0", tk.END)
            self.original_text.insert("1.0", path.read_text(encoding="utf-8", errors="replace"))

    def start_workflow(self, mode):
        if self.running:
            return
        if mode == 1:
            prompt = self.prompt_text.get("1.0", "end-1c").strip()
            if not prompt:
                messagebox.showerror("Missing prompt", "Enter a programming problem first.")
                return
            command = ["--mode", "1", "--prompt", prompt, "--test-file", self.mode1_tests.get().strip(), "--output", self.mode1_output.get().strip(), "--num-candidates", self.mode1_count.get().strip()]
        else:
            source = self.original_text.get("1.0", "end-1c").strip()
            if not source:
                messagebox.showerror("Missing source", "Choose a Python file or enter source code first.")
                return
            source_path = ROOT / "outputs" / "temp" / "desktop_input.py"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text(source, encoding="utf-8")
            command = ["--mode", "2", "--input-file", str(source_path), "--test-file", self.mode2_tests.get().strip(), "--output", self.mode2_output.get().strip()]
        self.running = True
        self.mode1_button.configure(state="disabled")
        self.mode2_tab.winfo_children()
        self.write_log(f"Starting Mode {mode}...")
        threading.Thread(target=self.execute, args=(command, mode), daemon=True).start()

    def execute(self, command, mode):
        try:
            process = subprocess.Popen([sys.executable, "-m", "ecocode.main", *command], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            for line in process.stdout:
                self.events.put(("log", line.rstrip()))
            return_code = process.wait()
            self.events.put(("done", mode, return_code))
        except OSError as error:
            self.events.put(("error", str(error)))

    def process_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "log":
                    self.write_log(event[1])
                elif event[0] == "done":
                    self.finish_workflow(event[1], event[2])
                else:
                    self.write_log(f"ERROR: {event[1]}")
                    self.finish_workflow(0, 1)
        except queue.Empty:
            pass
        self.after(100, self.process_events)

    def finish_workflow(self, mode, return_code):
        self.running = False
        self.mode1_button.configure(state="normal")
        if return_code != 0:
            self.write_log(f"Workflow failed with exit code {return_code}.")
            return
        self.write_log("Workflow completed successfully.")
        if mode == 1:
            self.load_mode1_report()
        else:
            self.load_mode2_report()

    def load_mode1_report(self):
        report = self.read_report(self.mode1_output.get())
        if not report:
            return
        winner = report.get("winner") or {}
        profile = winner.get("profile") or {}
        self.mode1_summary.configure(text=f"Winner: {winner.get('id', 'None')}   |   Time: {profile.get('execution_time_ms', 'N/A')} ms   |   Energy: {profile.get('energy_joules', 'N/A')} J")
        self.mode1_code.delete("1.0", tk.END)
        self.mode1_code.insert("1.0", winner.get("source_code", ""))
        self.clear_tree(self.mode1_tree)
        for candidate in report.get("candidates", []):
            candidate_profile = candidate.get("profile") or {}
            self.mode1_tree.insert("", "end", values=(candidate.get("id"), "Yes" if candidate.get("is_valid") else "No", candidate_profile.get("execution_time_ms", "N/A"), candidate_profile.get("peak_memory_kb", "N/A"), candidate_profile.get("energy_joules", "N/A"), candidate.get("topsis_score", "N/A")))

    def load_mode2_report(self):
        report = self.read_report(self.mode2_output.get())
        if not report:
            return
        winner = report.get("winner") or {}
        self.mode2_summary.configure(text=f"Selected: {winner.get('id', 'None')}   |   Valid candidates: {report.get('valid_candidates', 0)}")
        optimized_path = ROOT / "outputs" / "rewritten_code" / "optimized_code.py"
        if optimized_path.exists():
            self.optimized_text.delete("1.0", tk.END)
            self.optimized_text.insert("1.0", optimized_path.read_text(encoding="utf-8", errors="replace"))
        self.clear_tree(self.mode2_tree)
        original = next((item for item in report.get("candidates", []) if item.get("id") == "Original"), {})
        rewritten = next((item for item in report.get("candidates", []) if item.get("id") == "Rewritten"), {})
        original_profile = original.get("profile") or {}
        rewritten_profile = rewritten.get("profile") or {}
        for key, label in (("execution_time_ms", "Execution time (ms)"), ("peak_memory_kb", "Memory (KB)"), ("energy_joules", "Energy (J)")):
            self.mode2_tree.insert("", "end", values=(label, original_profile.get(key, "N/A"), rewritten_profile.get(key, "N/A"), "See report"))

    def read_report(self, value):
        path = Path(value)
        if not path.exists():
            self.write_log(f"Report not found: {path}")
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            self.write_log(f"Could not read report: {error}")
            return None

    @staticmethod
    def clear_tree(tree):
        for item in tree.get_children():
            tree.delete(item)

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", tk.END)
        self.log.configure(state="disabled")

    def write_log(self, message):
        self.log.configure(state="normal")
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")


if __name__ == "__main__":
    EcoCodeStudio().mainloop()
