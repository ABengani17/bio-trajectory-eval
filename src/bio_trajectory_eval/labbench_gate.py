from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from bio_trajectory_eval.checks import scan_package
from bio_trajectory_eval.schema import Decision, Policy, ScanResult, load_package, load_policy

try:
    import labbench as lb
except ModuleNotFoundError:  # pragma: no cover - exercised only without optional dependency
    lb = None


BaseDevice = lb.Device if lb is not None else object


class BiosecurityGate(BaseDevice):
    """labbench-compatible preflight gate for automation packages.

    Use this as a virtual device in a labbench Rack before opening instruments
    or scheduling a liquid-handler run. It performs local metadata checks and
    can fail closed on block decisions.
    """

    def __init__(
        self,
        policy_path: str | Path | None = None,
        audit_log: str | Path | None = None,
        fail_on_review: bool = False,
    ):
        if lb is not None:
            super().__init__()
        self.policy_path = str(policy_path) if policy_path is not None else ""
        self.audit_log = str(audit_log) if audit_log is not None else ""
        self.fail_on_review = fail_on_review
        self._isopen = False
        self.last_result: ScanResult | None = None

    @property
    def isopen(self) -> bool:
        return self._isopen

    def open(self) -> None:
        self._isopen = True

    def close(self) -> None:
        self._isopen = False

    def scan(self, manifest: str | Path, policy: Policy | None = None) -> ScanResult:
        active_policy = policy or load_policy(self.policy_path or None)
        result = scan_package(load_package(manifest), active_policy)
        self.last_result = result
        self._write_audit_record(manifest, result)
        return result

    def assert_clearance(self, manifest: str | Path, policy: Policy | None = None) -> ScanResult:
        result = self.scan(manifest, policy)
        should_fail = result.summary.decision == Decision.BLOCK
        if self.fail_on_review and result.summary.decision == Decision.REVIEW:
            should_fail = True
        if should_fail:
            raise RuntimeError(
                f"biosecurity preflight {result.summary.decision.value} for "
                f"{result.summary.package_id}: {result.summary.finding_count} findings"
            )
        return result

    def _write_audit_record(self, manifest: str | Path, result: ScanResult) -> None:
        if not self.audit_log:
            return
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "manifest": str(manifest),
            "result": result.model_dump(mode="json"),
        }
        path = Path(self.audit_log)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(dump_json_like(record) + "\n")


def dump_json_like(record: dict) -> str:
    import json

    return json.dumps(record, sort_keys=True)
