from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "tools" / "build_shared_release.py"
SPEC = importlib.util.spec_from_file_location("build_shared_release", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
shared_release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shared_release)


def _write_spec(path: Path, sources: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps(
            {
                "dataset_license": "CC-BY-4.0",
                "schema_version": 1,
                "sources": sources,
            }
        ),
        encoding="utf-8",
    )


def test_manifest_deduplicates_aliases_and_records_paper_alignment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for repository in ("repo-a", "repo-b"):
        payload = tmp_path / repository / "data" / "same.csv"
        payload.parent.mkdir(parents=True)
        payload.write_text("value\n1\n", encoding="utf-8")

    spec_path = tmp_path / "sources.json"
    _write_spec(
        spec_path,
        [
            {
                "attribution": ["Falas et al."],
                "collection_id": "shared",
                "evidence_status": "verified",
                "paper_alignment_note": "Exact paper input.",
                "paths": ["data/same.csv"],
                "provenance": "author-generated",
                "repository": "repo-a",
                "rights_status": "author-owned-approved",
            },
            {
                "attribution": ["GEFCom2012 (Tao Hong et al.)"],
                "collection_id": "shared",
                "evidence_status": "verified-duplicate-preservation-copy",
                "paths": ["data/same.csv"],
                "provenance": "preservation-copy",
                "repository": "repo-b",
                "rights_status": "author-owned-approved",
            },
        ],
    )
    monkeypatch.setattr(shared_release, "_commit", lambda _path: "abc123")

    manifest = shared_release.build_manifest(tmp_path, spec_path)

    assert manifest["upload_ready"] is True
    assert manifest["target"]["record_id"] == 21533592
    assert manifest["target"]["status"] == "draft"
    assert manifest["target"]["version_doi"] == "10.5281/zenodo.21533592"
    assert manifest["summary"]["unique_files"] == 1
    assert manifest["summary"]["declared_aliases"] == 2
    assert manifest["files"][0]["block_reasons"] == []
    assert manifest["files"][0]["license"] == "CC-BY-4.0"
    assert manifest["files"][0]["aliases"][0]["paper_alignment_note"] == (
        "Exact paper input."
    )
    # Credit required by CC BY travels with the file, unioned across aliases.
    assert manifest["files"][0]["attribution"] == [
        "Falas et al.",
        "GEFCom2012 (Tao Hong et al.)",
    ]


def test_manifest_explains_rights_and_evidence_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = tmp_path / "repo" / "data.csv"
    payload.parent.mkdir()
    payload.write_text("value\n1\n", encoding="utf-8")
    spec_path = tmp_path / "sources.json"
    _write_spec(
        spec_path,
        [
            {
                "collection_id": "blocked",
                "evidence_status": "unverified",
                "paths": ["data.csv"],
                "provenance": "unknown",
                "repository": "repo",
                "rights_status": "pending-permission",
            }
        ],
    )
    monkeypatch.setattr(shared_release, "_commit", lambda _path: "abc123")

    manifest = shared_release.build_manifest(tmp_path, spec_path)

    assert manifest["upload_ready"] is False
    assert manifest["files"][0]["block_reasons"] == [
        "rights:pending-permission",
        "evidence:unverified",
        "attribution:missing",
    ]
    assert manifest["files"][0]["license"] is None


def test_approved_payload_without_attribution_stays_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CC BY is only valid with credit, so cleared rights alone are not enough."""
    payload = tmp_path / "repo" / "data.csv"
    payload.parent.mkdir()
    payload.write_text("value\n1\n", encoding="utf-8")
    spec_path = tmp_path / "sources.json"
    _write_spec(
        spec_path,
        [
            {
                "collection_id": "cleared-but-uncredited",
                "evidence_status": "verified",
                "paths": ["data.csv"],
                "provenance": "author-generated",
                "repository": "repo",
                "rights_status": "author-owned-approved",
            }
        ],
    )
    monkeypatch.setattr(shared_release, "_commit", lambda _path: "abc123")

    manifest = shared_release.build_manifest(tmp_path, spec_path)

    assert manifest["upload_ready"] is False
    assert manifest["files"][0]["upload_eligible"] is False
    assert manifest["files"][0]["block_reasons"] == ["attribution:missing"]
    assert manifest["files"][0]["license"] is None


def test_fdia_attack_area_is_read_from_json_sidecar(tmp_path: Path) -> None:
    payload = tmp_path / "attacks.npz"
    payload.write_bytes(b"dataset")
    payload.with_suffix(".json").write_text(
        '{"metadata": {"attack_areas": [[3, 1, 2], [3, 1, 2]]}}',
        encoding="utf-8",
    )

    assert shared_release._fdia_attack_area(payload) == [1, 2, 3]
