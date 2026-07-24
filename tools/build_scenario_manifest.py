"""Build or verify the transient-scenario provenance manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

import scipy.io

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = REPO_ROOT / "datasets" / "powerworld-ieee118" / "transient-simulations"
DEFAULT_OUTPUT = SCENARIO_ROOT / "manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest() -> dict:
    base_dataset = (
        REPO_ROOT
        / "datasets/psse-via-dnns/original/pypower-ieee118/combined_dataset.mat"
    )
    base_shapes = {
        name: list(shape)
        for name, shape, _ in scipy.io.whosmat(base_dataset)
        if name in {"features", "labels"}
    }
    scenarios: dict[str, dict] = {}
    for scenario_dir in sorted(path for path in SCENARIO_ROOT.iterdir() if path.is_dir()):
        required = {
            "powerworld_export": scenario_dir / "raw_export.xlsx",
            "mat_dataset": scenario_dir / "dataset.mat",
            "csv_dataset": scenario_dir / "dataset.csv",
        }
        missing = [path for path in required.values() if not path.is_file()]
        if missing:
            raise FileNotFoundError(
                f"{scenario_dir.name} is missing required artifacts: "
                + ", ".join(str(path) for path in missing)
            )

        shapes = {
            name: list(shape)
            for name, shape, _ in scipy.io.whosmat(required["mat_dataset"])
            if name in {"features", "labels"}
        }
        scenarios[scenario_dir.name] = {
            "schema": {
                "features": "[P_1..P_118,Q_1..Q_118] per unit",
                "labels": "[V_1..V_118,theta_1..theta_118] with theta in radians",
                "shapes": shapes,
            },
            "files": {
                role: {
                    "path": str(path.relative_to(REPO_ROOT)),
                    "sha256": _sha256(path),
                }
                for role, path in required.items()
            },
        }

    return {
        "schema_version": 1,
        "converter": "tools/powerworld_to_dataset.py",
        "matlab_reference": "datasets/powerworld-ieee118/matlab/powerworld_to_dataset.m",
        "bus_count": 118,
        "base_mva": 100,
        "skip_initial_numeric_rows": 2,
        "base_dataset": {
            "path": str(base_dataset.relative_to(REPO_ROOT)),
            "sha256": _sha256(base_dataset),
            "shapes": base_shapes,
        },
        "scenarios": scenarios,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rendered = json.dumps(build_manifest(), indent=2, sort_keys=True) + "\n"
    if args.check:
        current = args.output.read_text(encoding="utf-8") if args.output.is_file() else ""
        if current != rendered:
            raise SystemExit(f"Scenario manifest is stale: {args.output}")
        print(f"Scenario manifest is current: {args.output}")
        return 0

    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
