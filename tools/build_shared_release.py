"""Build the deduplicated cross-repository Zenodo dataset inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = REPO_ROOT / "datasets" / "shared-release-sources.json"
DEFAULT_OUTPUT = REPO_ROOT / "datasets" / "shared-release-manifest.json"
ALLOWED_SUFFIXES = {".csv", ".json", ".mat", ".npz", ".npy", ".txt", ".xlsx"}
VERIFIED_EVIDENCE = {
    "verified",
    "verified-duplicate-preservation-copy",
    "verified-experiment-artifact",
    "verified-generated-at-runtime",
}
APPROVED_RIGHTS = {"approved", "author-owned-approved"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _commit(repository_root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        text=True,
    ).strip()


def _zenodo_key(collection_id: str, path: Path) -> str:
    safe_path = re.sub(r"[^A-Za-z0-9._-]+", "__", path.as_posix())
    return f"{collection_id}__{safe_path}"


def _fdia_attack_area(path: Path) -> list[int] | None:
    sidecar = path if path.suffix.lower() == ".json" else path.with_suffix(".json")
    if not sidecar.is_file():
        return None
    with sidecar.open(encoding="utf-8") as handle:
        prefix = handle.read(64 * 1024)
    match = re.search(
        r'"attack_areas"\s*:\s*\[\s*\[([^\]]+)\]',
        prefix,
    )
    if match is None:
        return None
    return sorted(int(value) for value in re.findall(r"-?\d+", match.group(1)))


def _source_paths(repository_root: Path, source: dict[str, Any]) -> list[Path]:
    paths = [repository_root / relative for relative in source.get("paths", [])]
    for pattern in source.get("glob_paths", []):
        matches = sorted(repository_root.glob(pattern))
        if not matches:
            raise ValueError(
                f"No files matched {source['repository']}:{pattern}"
            )
        paths.extend(path for path in matches if path.is_file())
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing declared release source(s): "
            + ", ".join(str(path) for path in missing)
        )
    return sorted(set(paths))


def build_manifest(workspace_root: Path, spec_path: Path) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    aliases_by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    file_info: dict[str, dict[str, Any]] = {}
    empty_collections: list[dict[str, Any]] = []

    for source in spec["sources"]:
        repository_root = workspace_root / source["repository"]
        if not repository_root.is_dir():
            raise FileNotFoundError(f"Missing repository: {repository_root}")
        source_paths = _source_paths(repository_root, source)
        if not source_paths:
            empty_collections.append(
                {
                    "collection_id": source["collection_id"],
                    "evidence_status": source["evidence_status"],
                    "repository": source["repository"],
                    "rights_status": source["rights_status"],
                }
            )
            continue

        commit = _commit(repository_root)
        for path in source_paths:
            if path.suffix.lower() not in ALLOWED_SUFFIXES:
                raise ValueError(f"Source-code or unsupported file in inventory: {path}")
            relative = path.relative_to(repository_root)
            digest = _sha256(path)
            alias = {
                "collection_id": source["collection_id"],
                "evidence_status": source["evidence_status"],
                "path": relative.as_posix(),
                "provenance": source["provenance"],
                "repository": source["repository"],
                "source_commit": commit,
                "rights_status": source["rights_status"],
            }
            if "paper_alignment_note" in source:
                alias["paper_alignment_note"] = source["paper_alignment_note"]
            if source["collection_id"] == "ieee118-fdia":
                attack_area = _fdia_attack_area(path)
                if attack_area is not None:
                    alias["attack_area_zero_based"] = attack_area
            aliases_by_hash[digest].append(alias)
            file_info.setdefault(
                digest,
                {
                    "bytes": path.stat().st_size,
                    "sha256": digest,
                    "source_path": path,
                },
            )

    files = []
    for digest, aliases in sorted(aliases_by_hash.items()):
        collection_ids = sorted({alias["collection_id"] for alias in aliases})
        rights = sorted({alias["rights_status"] for alias in aliases})
        evidence = sorted({alias["evidence_status"] for alias in aliases})
        upload_eligible = (
            all(status in APPROVED_RIGHTS for status in rights)
            and all(status in VERIFIED_EVIDENCE for status in evidence)
        )
        block_reasons = [
            *(f"rights:{status}" for status in rights if status not in APPROVED_RIGHTS),
            *(
                f"evidence:{status}"
                for status in evidence
                if status not in VERIFIED_EVIDENCE
            ),
        ]
        canonical = aliases[0]
        info = file_info[digest]
        files.append(
            {
                "aliases": aliases,
                "block_reasons": block_reasons,
                "bytes": info["bytes"],
                "collection_ids": collection_ids,
                "evidence_statuses": evidence,
                "license": spec["dataset_license"] if upload_eligible else None,
                "rights_statuses": rights,
                "sha256": digest,
                "upload_eligible": upload_eligible,
                "zenodo_key": _zenodo_key(
                    collection_ids[0],
                    Path(canonical["repository"]) / canonical["path"],
                ),
            }
        )

    blocked = [item for item in files if not item["upload_eligible"]]
    return {
        "schema_version": 1,
        "target": {
            "concept_doi": "10.5281/zenodo.20744597",
            "file_policy": "dataset-payloads-only",
            "license": spec["dataset_license"],
            "record_id": 21533592,
            "resource_type": "dataset",
            "status": "draft",
            "version_doi": "10.5281/zenodo.21533592",
        },
        "summary": {
            "blocked_unique_files": len(blocked),
            "declared_aliases": sum(len(item["aliases"]) for item in files),
            "empty_or_runtime_generated_collections": len(empty_collections),
            "total_bytes_unique": sum(item["bytes"] for item in files),
            "unique_files": len(files),
            "upload_eligible_unique_files": len(files) - len(blocked),
        },
        "empty_or_runtime_generated_collections": empty_collections,
        "upload_ready": bool(files) and not blocked,
        "files": files,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=REPO_ROOT.parent,
        help="Directory containing the sibling experiment repositories.",
    )
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = build_manifest(args.workspace_root.resolve(), args.spec.resolve())
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.check:
        current = args.output.read_text(encoding="utf-8") if args.output.is_file() else ""
        if current != rendered:
            raise SystemExit(f"Shared release manifest is stale: {args.output}")
        print(f"Shared release manifest is current: {args.output}")
        return 0
    args.output.write_text(rendered, encoding="utf-8")
    print(
        f"Wrote {args.output}: {manifest['summary']['unique_files']} unique files, "
        f"{manifest['summary']['blocked_unique_files']} blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
