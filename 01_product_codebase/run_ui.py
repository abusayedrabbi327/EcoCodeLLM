import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    command = [
        sys.executable,
        str(ROOT / "gui_professional.py"),
    ]

    print("Launching EcoCode Desktop GUI...")
    print("Close the GUI window or press Ctrl+C in terminal to stop.")

    process = subprocess.Popen(command, cwd=ROOT, env=os.environ.copy())
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()


if __name__ == "__main__":
    main()
