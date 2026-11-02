"""Verify retained physical pin/net assignments against the pre-WAGO V2 source."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "682481f"
before_bytes = subprocess.check_output(
    ["git", "show", BASELINE + ":artifacts/v2/source.circuit.json"], cwd=ROOT
)
after_bytes = (ROOT / "artifacts/v2/source.circuit.json").read_bytes()


def physical_nets(raw):
    data = json.loads(raw)
    components = {e["source_component_id"]: e["name"] for e in data if e["type"] == "source_component"}
    ports = {e["source_port_id"]: e for e in data if e["type"] == "source_port"}
    nets = {e["source_net_id"]: e["name"] for e in data if e["type"] == "source_net"}
    result = {}
    for trace in data:
        if trace["type"] != "source_trace":
            continue
        names = {nets[n] for n in trace.get("connected_source_net_ids", []) if n in nets}
        if len(names) > 1:
            raise ValueError("Named source nets shorted: " + str(names))
        if not names:
            continue
        for port_id in trace.get("connected_source_port_ids", []):
            port = ports[port_id]
            name = components[port["source_component_id"]]
            if name.startswith("J_MOTOR"):
                continue
            key = (name, port["pin_number"])
            net = next(iter(names))
            if key in result and result[key] != net:
                raise ValueError("Physical pin on two named nets: " + str(key))
            result[key] = net
    return result


before, after = physical_nets(before_bytes), physical_nets(after_bytes)
changes = [
    {"component": n, "pin": p, "before": before.get((n, p)), "after": after.get((n, p))}
    for n, p in sorted(before.keys() | after.keys())
    if before.get((n, p)) != after.get((n, p))
]
receipt = {
    "passed": not changes,
    "baseline_commit": BASELINE,
    "baseline_source_sha256": hashlib.sha256(before_bytes).hexdigest(),
    "source_sha256": hashlib.sha256(after_bytes).hexdigest(),
    "non_motor_physical_pin_nets_checked": len(before),
    "changed_pin_nets": changes,
    "excluded_change": "Two Phoenix terminals replaced by one WAGO; motor pin/phase mapping checked by check-v2.py",
    "scope": "Named-net connectivity at physical pins; not copper or fabrication qualification.",
}
(ROOT / "artifacts/v2/net-preservation.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
if changes:
    raise SystemExit(1)
