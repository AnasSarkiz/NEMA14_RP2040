"""Read the exact reviewed diagnostics baseline from Git, without /tmp dependencies."""
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "56222094968d6ebefd37adfe6f32623149403b10"
def baseline_bytes(relative):
    return subprocess.check_output(["git", "show", f"{BASELINE_COMMIT}:{relative}"], cwd=ROOT)
