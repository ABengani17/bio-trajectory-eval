from pathlib import Path

try:
    import labbench as lb
except ModuleNotFoundError as exc:
    raise SystemExit("Install labbench to run this demo: python -m pip install labbench") from exc

from bio_trajectory_eval.labbench_gate import BiosecurityGate


ROOT = Path(__file__).resolve().parents[1]


class AutomationRack(lb.Rack):
    gate = BiosecurityGate(
        policy_path=ROOT / "examples" / "policy_default.json",
        audit_log=ROOT / "results" / "biosecurity_gate_audit.jsonl",
    )

    def preflight(self, manifest: str):
        return self.gate.assert_clearance(manifest)

    def run_liquid_handler(self):
        # Connect the real liquid-handler device here after preflight passes.
        return "scheduled"


if __name__ == "__main__":
    manifest = ROOT / "examples" / "pass_inert_opentrons.json"
    with AutomationRack() as rack:
        rack.preflight(manifest)
        print(rack.run_liquid_handler())
