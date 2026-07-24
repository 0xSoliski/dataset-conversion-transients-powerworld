from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest
import scipy.io
from openpyxl import Workbook

MODULE_PATH = Path(__file__).parents[1] / "tools" / "powerworld_to_dataset.py"
SPEC = importlib.util.spec_from_file_location("powerworld_to_dataset", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
converter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(converter)

REPO_ROOT = Path(__file__).parents[1]
SCENARIO_ROOT = REPO_ROOT / "datasets" / "powerworld-ieee118" / "transient-simulations"


@pytest.mark.parametrize(
    "scenario",
    (
        "three-phase-fault-bus19",
        "load-increase-20-to-27",
        "gen26_shutdown",
        "gen59_shutdown",
    ),
)
def test_python_converter_matches_tracked_mat_dataset(scenario):
    scenario_dir = SCENARIO_ROOT / scenario
    raw_export = scenario_dir / "raw_export.xlsx"
    mat_dataset = scenario_dir / "dataset.mat"
    available = (raw_export.is_file(), mat_dataset.is_file())
    if not any(available):
        pytest.skip("requires the Zenodo transient/fault dataset collection")
    if not all(available):
        pytest.fail(f"incomplete Zenodo scenario payload: {scenario}")

    _, features, labels = converter.read_powerworld_export(raw_export)
    expected = scipy.io.loadmat(
        mat_dataset,
        variable_names=("features", "labels"),
    )

    np.testing.assert_allclose(features, expected["features"], rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(labels, expected["labels"], rtol=0.0, atol=1e-12)


def test_converter_rejects_unexpected_headers(tmp_path):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = converter.SHEET_NAME
    worksheet.append([converter.SHEET_NAME])
    worksheet.append(["Time", "unexpected"])
    worksheet.append([0.0, 1.0])
    path = tmp_path / "invalid.xlsx"
    workbook.save(path)

    with pytest.raises(ValueError, match="expected"):
        converter.read_powerworld_export(path, bus_count=1)


def test_write_dataset_round_trip(tmp_path):
    features = np.array([[1.0, 2.0]], dtype=np.float64)
    labels = np.array([[0.99, 0.01]], dtype=np.float64)

    mat_path, csv_path = converter.write_dataset(
        tmp_path / "dataset",
        features=features,
        labels=labels,
    )

    loaded = scipy.io.loadmat(mat_path)
    np.testing.assert_array_equal(loaded["features"], features)
    np.testing.assert_array_equal(loaded["labels"], labels)
    np.testing.assert_allclose(
        np.atleast_2d(np.loadtxt(csv_path, delimiter=",")),
        np.hstack((features, labels)),
    )
