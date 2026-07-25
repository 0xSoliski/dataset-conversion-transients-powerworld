"""Deterministic CPU checks for the release metadata and published tree.

Every repository in this publication family ships this file unchanged. The
checks need no dataset, trained model, or deep-learning install, so a
source-only checkout is validated on the CI baseline (Linux, Python 3.10).
"""

from __future__ import annotations

import ast
import json

import pytest

from conftest import REPO_ROOT, published_files, source_id, tracked_sources

CONCEPT_DOI = "10.5281/zenodo.20744597"
VERSION_DOI = "10.5281/zenodo.21533592"
RECORD_ID = 21533592

# Real data lives on Zenodo and trained models are rebuilt from source, so
# neither may ever enter a published tree.
PAYLOAD_SUFFIXES = frozenset(
    {
        ".ckpt",
        ".csv",
        ".h5",
        ".keras",
        ".mat",
        ".npy",
        ".npz",
        ".pdf",
        ".pkl",
        ".png",
        ".pt",
        ".pth",
        ".pwb",
        ".pwd",
        ".xlsx",
    }
)

# Release-management notes that were folded into the README. They must not
# reappear: the public tree carries a README, a licence, and citation metadata.
RETIRED_DOCUMENTS = (
    "ARCHIVAL_STATUS.md",
    "CHANGELOG.md",
    "DATASET_CONTRACT.md",
    "PAPER_EVIDENCE_MAP.md",
    "PROJECT_SCOPE.md",
    "RELEASE_READINESS.md",
    "REPRODUCIBILITY.md",
    "ZENODO_RECORDS.md",
)

# The shared README outline, so the seven repositories read as one family.
README_SECTIONS = (
    "## Paper",
    "## Data",
    "## Installation",
    "## Reproducing the results",
    "## Repository layout",
    "## Citation",
    "## License",
)


def test_dataset_pointer_targets_the_shared_dataset_record() -> None:
    pointer = json.loads((REPO_ROOT / "DATASET_SOURCE.json").read_text(encoding="utf-8"))
    record = pointer["record"]

    assert pointer["schema_version"] == 1
    assert record["concept_doi"] == CONCEPT_DOI
    assert record["version_doi"] == VERSION_DOI
    assert record["record_id"] == RECORD_ID
    assert record["resource_type"] == "dataset"
    assert record["file_policy"] == "dataset-payloads-only"
    assert pointer["collections"]


def test_every_declared_collection_is_described() -> None:
    """A collection with no id or relationship cannot be resolved on Zenodo."""
    pointer = json.loads((REPO_ROOT / "DATASET_SOURCE.json").read_text(encoding="utf-8"))

    for collection in pointer["collections"]:
        assert collection["id"]
        assert collection["relationship"]


def test_license_is_mit() -> None:
    assert "MIT License" in (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")


def test_citation_metadata_declares_mit_and_a_repository() -> None:
    citation = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    fields = {
        line.split(":", 1)[0]
        for line in citation.splitlines()
        if line and not line.startswith((" ", "-", "#"))
    }

    assert {"cff-version", "title", "authors", "license", "repository-code"} <= fields
    assert "license: MIT" in citation


@pytest.mark.parametrize("section", README_SECTIONS)
def test_readme_follows_the_shared_outline(section: str) -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert section in readme


def test_release_documentation_stays_minimal() -> None:
    """Release-process notes belong in the README, not in separate files."""
    resurrected = [name for name in RETIRED_DOCUMENTS if (REPO_ROOT / name).is_file()]

    assert resurrected == []


def test_tracked_sources_are_discovered() -> None:
    assert tracked_sources()


@pytest.mark.parametrize("source", tracked_sources(), ids=source_id)
def test_source_parses(source) -> None:
    """A syntax regression in any published script fails CI immediately."""
    ast.parse(source.read_text(encoding="utf-8"), filename=str(source))


def test_no_dataset_or_model_payloads_are_published() -> None:
    offenders = [
        source_id(path)
        for path in published_files()
        if path.suffix.lower() in PAYLOAD_SUFFIXES
    ]

    assert offenders == []
