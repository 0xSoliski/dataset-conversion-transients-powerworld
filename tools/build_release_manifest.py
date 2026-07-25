"""Build or verify the Zenodo-oriented dataset release manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = REPO_ROOT / "datasets"
DEFAULT_OUTPUT = DATASET_ROOT / "release-manifest.json"
DATASET_LICENSE = "CC-BY-4.0"
# A redistribution status is resolved once it is either cleared for the record
# or explicitly withheld from it. Anything else blocks publication.
RESOLVED_REDISTRIBUTION = frozenset({"approved", "excluded-upstream-original"})

PAYLOAD_SUFFIXES = {
    ".csv",
    ".mat",
    ".pwb",
    ".pwd",
    ".txt",
    ".xlsx",
    ".zip",
}
ARCHIVE_MEMBER_SUFFIXES = PAYLOAD_SUFFIXES - {".zip"}
BASE_COLLECTION_GROUPS = {
    "gefcom2012-upstream",
    "psse-via-dnns-upstream",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_payload(path: Path) -> tuple[str, str, str]:
    """Return group, provenance class, and redistribution status.

    Author-owned derived data is ``approved`` for the CC BY dataset record.
    Files obtained unmodified from an upstream provider are
    ``excluded-upstream-original``: they stay in the local tree because the
    lineage checks need them, but this project does not redistribute them.
    """

    relative = path.relative_to(DATASET_ROOT)
    parts = relative.parts

    if parts[:2] == ("gefcom2012", "original"):
        return "gefcom2012-upstream", "third-party", "excluded-upstream-original"
    if parts[:2] in {
        ("powerworld-ieee118", "case"),
        ("powerworld-ieee118", "reference"),
    }:
        return "kios-powerworld-case", "third-party", "excluded-upstream-original"
    # Derived from the GEFCom2012 load profiles by this project's own
    # AC-power-flow sampling, so it is author-owned rather than upstream.
    if parts[:2] == ("psse-via-dnns", "original"):
        return "ieee118-operating-points", "project-derived", "approved"
    if parts[:2] == ("powerworld-ieee118", "import-files"):
        return "powerworld-import-files", "project-derived", "approved"
    if parts[:2] == ("powerworld-ieee118", "transient-simulations"):
        if path.name == "raw_export.xlsx":
            group = "powerworld-transient-raw-exports"
        else:
            group = "powerworld-transient-derived-datasets"
        return group, "project-derived", "approved"

    raise ValueError(f"Unclassified dataset payload: {relative}")


def validate_dataset_payload(path: Path) -> None:
    """Reject code or repository content from the Zenodo payload inventory."""

    suffix = path.suffix.lower()
    if suffix not in PAYLOAD_SUFFIXES:
        raise ValueError(f"Not an allowed dataset payload: {path}")
    if suffix != ".zip":
        return

    with zipfile.ZipFile(path) as archive:
        invalid_members = [
            member
            for member in archive.namelist()
            if not member.endswith("/")
            and Path(member).suffix.lower() not in ARCHIVE_MEMBER_SUFFIXES
        ]
    if invalid_members:
        raise ValueError(
            f"Dataset archive contains non-data files: {path}: "
            f"{', '.join(invalid_members)}"
        )


def collection_id(group: str) -> str:
    """Map provenance groups into the shared Zenodo collection layout."""

    if group in BASE_COLLECTION_GROUPS:
        return "ieee118-base-state-estimation"
    return "ieee118-transient-and-fault"


def zenodo_key(path: Path) -> str:
    """Return a unique flat filename suitable for a Zenodo dataset record."""

    relative = path.relative_to(DATASET_ROOT)
    return "__".join(relative.parts)


def iter_payloads() -> Iterable[Path]:
    for path in sorted(DATASET_ROOT.rglob("*")):
        if path.is_file() and path.suffix.lower() in PAYLOAD_SUFFIXES:
            validate_dataset_payload(path)
            yield path


def build_manifest() -> dict:
    files = []
    for path in iter_payloads():
        group, provenance, redistribution = classify_payload(path)
        files.append(
            {
                "bytes": path.stat().st_size,
                "collection_id": collection_id(group),
                "group": group,
                "intended_license": DATASET_LICENSE,
                "license": DATASET_LICENSE if redistribution == "approved" else None,
                "path": str(path.relative_to(REPO_ROOT)),
                "provenance": provenance,
                "redistribution": redistribution,
                "sha256": _sha256(path),
                "target_storage": "zenodo-dataset-record",
                "upload_eligible": redistribution == "approved",
                "zenodo_key": zenodo_key(path),
            }
        )

    return {
        "schema_version": 1,
        "target_dataset_record": {
            "collection_layout": "DATASET_COLLECTIONS.md",
            "concept_doi": "10.5281/zenodo.20744597",
            "file_policy": "dataset-payloads-only",
            "github_integration": False,
            "license": DATASET_LICENSE,
            "license_scope": "rights-cleared-payloads-only",
            "record_id": 21533592,
            "repository_archives_allowed": False,
            "resource_type": "dataset",
            "status": "draft",
            "version_doi": "10.5281/zenodo.21533592",
        },
        "publication_gate": (
            "Do not publish a new dataset version while any file still has an "
            "unresolved redistribution status. Files marked "
            "excluded-upstream-original are resolved: they are deliberately "
            "not redistributed."
        ),
        "upload_ready": bool(files)
        and all(item["redistribution"] in RESOLVED_REDISTRIBUTION for item in files),
        "files": files,
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
            raise SystemExit(f"Release manifest is stale: {args.output}")
        print(f"Release manifest is current: {args.output}")
        return 0

    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
