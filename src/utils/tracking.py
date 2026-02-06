"""
Utilities for lightweight run tracking.

The project stores run metadata and metrics as JSON files under:
    models/runs/<run_id>/

This is intentionally simple (no external services) but provides traceability
similar to experiment tracking tools.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


RUNS_DIR = Path("models") / "runs"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_run_dir(run_id: str) -> Path:
    """Create (or reuse) the folder for a run and return its path."""
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)


def log_run_metadata(run_id: str, metadata: Dict[str, Any]) -> None:
    """Write run-level metadata to models/runs/<run_id>/run.json."""
    run_dir = create_run_dir(run_id)
    payload = {"run_id": run_id, "created_at": _utc_now_iso(), **metadata}
    _write_json(run_dir / "run.json", payload)


def log_metrics(run_id: str, metrics: Dict[str, Any]) -> None:
    """Write metrics to models/runs/<run_id>/metrics.json."""
    run_dir = create_run_dir(run_id)
    payload = {"run_id": run_id, "created_at": _utc_now_iso(), **metrics}
    _write_json(run_dir / "metrics.json", payload)
