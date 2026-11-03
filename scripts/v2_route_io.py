"""Use the saved V2 routed board unless an explicit trial file is selected."""
from pathlib import Path
import sys

if not any(q=='--source' or q.startswith('--source=') for q in sys.argv[1:]):
    sys.argv.extend(['--source',str(Path(__file__).resolve().parents[1]/'artifacts/v2/routing/freerouted.circuit.json')])
import verify_supplier_connectivity as g
