"""
Lightweight run tracking utilities.

Stores run metadata and metrics as JSON files under models/runs/<run_id>/.
"""

import json
import os
from datetime import datetime
from typing import Dict


def create_run_dir(run_id: str) -> str:
    base = os.path.join("models", "runs", run_id)
    os.makedirs(base, exist_ok=True)
    return base


def log_run_metadata(run_id: str, metadata: Dict) -> None:
    run_dir = create_run_dir(run_id)
    path = os.path.join(run_dir, "run.json")

    payload = {
        "run_id": run_id,
        "created_at": datetime.utcnow().isoformat(),
        **metadata,
    }

    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def log_metrics(run_id: str, metrics: Dict) -> None:
    run_dir = create_run_dir(run_id)
    path = os.path.join(run_dir, "metrics.json")

    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)
