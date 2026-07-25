from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "tools" / "build_release_manifest.py"
SPEC = importlib.util.spec_from_file_location("build_release_manifest", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
release_manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_manifest)

REPO_ROOT = Path(__file__).parents[1]


def checked_manifest() -> dict:
    path = REPO_ROOT / "datasets/release-manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_payload_classification_distinguishes_source_and_derived_data():
    source = (
        REPO_ROOT
        / "datasets/psse-via-dnns/original/pypower-ieee118/combined_dataset.mat"
    )
    derived = (
        REPO_ROOT
        / "datasets/powerworld-ieee118/transient-simulations/"
        "gen26_shutdown/dataset.mat"
    )

    upstream = REPO_ROOT / "datasets/gefcom2012/original/GEFCOM2012_Data/Load/Holiday_List.csv"

    assert release_manifest.classify_payload(source) == (
        "ieee118-operating-points",
        "project-derived",
        "approved",
    )
    assert release_manifest.classify_payload(derived) == (
        "powerworld-transient-derived-datasets",
        "project-derived",
        "approved",
    )
    # Files taken unmodified from upstream are never redistributed by this record.
    assert release_manifest.classify_payload(upstream) == (
        "gefcom2012-upstream",
        "third-party",
        "excluded-upstream-original",
    )


def test_release_manifest_is_current():
    manifest = checked_manifest()
    payloads = [REPO_ROOT / item["path"] for item in manifest["files"]]
    available = [path.is_file() for path in payloads]
    if not any(available):
        pytest.skip("requires the complete Zenodo dataset payload")
    if not all(available):
        pytest.fail("local Zenodo payload is incomplete")

    assert manifest == release_manifest.build_manifest()


def test_release_manifest_allows_only_dataset_payloads():
    manifest = checked_manifest()
    record = manifest["target_dataset_record"]

    assert record["resource_type"] == "dataset"
    assert record["concept_doi"] == "10.5281/zenodo.20744597"
    assert record["collection_layout"] == "DATASET_COLLECTIONS.md"
    assert record["record_id"] == 21533592
    assert record["status"] == "draft"
    assert record["version_doi"] == "10.5281/zenodo.21533592"
    assert record["file_policy"] == "dataset-payloads-only"
    assert record["github_integration"] is False
    assert record["repository_archives_allowed"] is False
    # Every file is either cleared for the record or explicitly withheld.
    assert manifest["upload_ready"] is True
    keys = [item["zenodo_key"] for item in manifest["files"]]
    assert len(keys) == len(set(keys))
    assert all(item["target_storage"] == "zenodo-dataset-record" for item in manifest["files"])
    assert all(
        item["redistribution"] in release_manifest.RESOLVED_REDISTRIBUTION
        for item in manifest["files"]
    )
    # Upstream originals stay in the inventory but carry no licence grant.
    withheld = [item for item in manifest["files"] if not item["upload_eligible"]]
    assert withheld
    assert all(item["redistribution"] == "excluded-upstream-original" for item in withheld)
    assert all(item["license"] is None for item in withheld)
    assert all(
        item["license"] == "CC-BY-4.0"
        for item in manifest["files"]
        if item["upload_eligible"]
    )
    assert {item["collection_id"] for item in manifest["files"]} == {
        "ieee118-base-state-estimation",
        "ieee118-transient-and-fault",
    }


def test_dataset_archive_rejects_code(tmp_path):
    archive_path = tmp_path / "payload.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("data.csv", "value\n1\n")
        archive.writestr("generate.py", "print('not dataset content')\n")

    with pytest.raises(ValueError, match="non-data files"):
        release_manifest.validate_dataset_payload(archive_path)
