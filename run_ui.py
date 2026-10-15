"""Root launcher for EcoCode Desktop Application.
Seamlessly redirects execution into 01_product_codebase.
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRODUCT_DIR = ROOT / "01_product_codebase"

def main() -> None:
    if not PRODUCT_DIR.exists():
        print(f"Error: Product directory not found at {PRODUCT_DIR}")
        sys.exit(1)

    target_script = PRODUCT_DIR / "run_ui.py"
    print(f"Starting EcoCode from: {target_script} ...")
    
    # Run target script with cwd set to PRODUCT_DIR
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PRODUCT_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    
    process = subprocess.Popen([sys.executable, str(target_script)], cwd=PRODUCT_DIR, env=env)
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()
