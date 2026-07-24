"""
Verification script for datasets/psse-via-dnns/original/pypower-ieee118.

Checks that the dataset is correctly derived from datasets/gefcom2012 as described
in arxiv:1811.06146:
  - IEEE 118-bus benchmark system (PyPower case118)
  - GEFCOM2012 load data, summed across all 20 zones, subsampled by factor 2
  - AC power flow (MATPOWER) solved for each normalized load instance
  - Measurements: forwarding-end Pij, Qij + all bus voltage magnitudes Vi
  - Labels: bus voltage magnitudes and angles

Usage:
    .venv/Scripts/python verify.py [--repo-root PATH]
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import scipy.io as sio
from pypower.case118 import case118


# ── paths ──────────────────────────────────────────────────────────────────────

def resolve_paths(repo_root: Path):
    ds = repo_root / "datasets"
    return {
        "psse_dir":    ds / "psse-via-dnns" / "original" / "pypower-ieee118",
        "gefcom_load": ds / "gefcom2012" / "original" / "GEFCOM2012_Data" / "Load" / "Load_history.csv",
    }


# ── helpers ────────────────────────────────────────────────────────────────────

def load_mat(path: Path, key: str = "data") -> np.ndarray:
    mat = sio.loadmat(str(path))
    return mat[key]


def load_gefcom_total_load(csv_path: Path) -> np.ndarray:
    """Return chronologically sorted array of total load (sum of all 20 zones) for
    every hour where all 20 zones report a value."""
    time_total: dict = defaultdict(float)
    time_count: dict = defaultdict(int)

    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            _, year, month, day = row[0], row[1], row[2], row[3]
            for hi, val_str in enumerate(row[4:], start=1):
                val_str = val_str.strip().replace(",", "")
                if val_str:
                    key = (int(year), int(month), int(day), hi)
                    time_total[key] += float(val_str)
                    time_count[key] += 1

    valid_keys = sorted(k for k, v in time_count.items() if v == 20)
    return np.array([time_total[k] for k in valid_keys])


# ── checks ─────────────────────────────────────────────────────────────────────

def check_system_dimensions(psse_dir: Path, case: dict) -> list[str]:
    """Verify bus/branch counts and measurement column layout."""
    issues = []
    n_buses    = case["bus"].shape[0]       # 118
    n_branches = case["branch"].shape[0]    # 186
    expected_meas   = n_branches * 2 + n_buses   # 490
    expected_labels = n_buses * 2               # 236

    meas   = load_mat(psse_dir / "Pij_Qij_Vi.mat")
    labels = load_mat(psse_dir / "V_magnitudes_angles.mat")
    injections = load_mat(psse_dir / "Pi_Qi_injections.mat")

    if meas.shape[1] != expected_meas:
        issues.append(f"Measurements: expected {expected_meas} cols, got {meas.shape[1]}")
    if labels.shape[1] != expected_labels:
        issues.append(f"Labels: expected {expected_labels} cols, got {labels.shape[1]}")
    if injections.shape[1] != expected_labels:
        issues.append(f"Injections: expected {expected_labels} cols, got {injections.shape[1]}")
    if meas.shape[0] != labels.shape[0]:
        issues.append(f"Row count mismatch: meas={meas.shape[0]}, labels={labels.shape[0]}")
    if injections.shape[0] != meas.shape[0]:
        issues.append(f"Row count mismatch: meas={meas.shape[0]}, injections={injections.shape[0]}")

    return issues


def check_slack_bus(psse_dir: Path, case: dict) -> list[str]:
    """Slack bus (Bus 69) must have constant vm=1.035 pu and va=pi/6 rad."""
    issues = []
    slack_idx = int(np.where(case["bus"][:, 1] == 3)[0][0])

    labels = load_mat(psse_dir / "V_magnitudes_angles.mat")
    n_buses = case["bus"].shape[0]
    vm = labels[:, slack_idx]
    va = labels[:, n_buses + slack_idx]

    expected_vm = case["bus"][slack_idx, 7]   # 1.035
    expected_va = np.radians(case["bus"][slack_idx, 8])  # pi/6

    if not np.allclose(vm, expected_vm, atol=1e-6):
        issues.append(f"Slack vm not constant at {expected_vm} pu: "
                      f"range=[{vm.min():.6f}, {vm.max():.6f}]")
    if not np.allclose(va, expected_va, atol=1e-6):
        issues.append(f"Slack va not constant at pi/6 rad: "
                      f"range=[{va.min():.6f}, {va.max():.6f}]")

    return issues


def check_vi_equals_vmag(psse_dir: Path, case: dict) -> list[str]:
    """Vi column in measurements must equal voltage magnitudes in labels."""
    issues = []
    n_buses    = case["bus"].shape[0]
    n_branches = case["branch"].shape[0]

    meas   = load_mat(psse_dir / "Pij_Qij_Vi.mat")
    labels = load_mat(psse_dir / "V_magnitudes_angles.mat")

    vi   = meas[:, n_branches * 2:]      # cols 373–490
    vmag = labels[:, :n_buses]           # cols 1–118

    max_diff = np.abs(vi - vmag).max()
    if max_diff > 1e-10:
        issues.append(f"Vi (measurements) != Vmag (labels): max diff = {max_diff:.2e}")

    return issues


def check_ac_power_flow(psse_dir: Path, case: dict, n_check: int = 1000) -> tuple[list[str], float, float]:
    """Reconstruct branch active/reactive flows from voltages; compare with stored Pij/Qij."""
    issues = []
    branch = case["branch"]
    fbus = (branch[:, 0] - 1).astype(int)
    tbus = (branch[:, 1] - 1).astype(int)
    r     = branch[:, 2]
    x     = branch[:, 3]
    b     = branch[:, 4]
    ratio = branch[:, 8].copy()
    ratio[ratio == 0] = 1.0

    n_branches = len(fbus)
    n_buses    = case["bus"].shape[0]

    meas   = load_mat(psse_dir / "Pij_Qij_Vi.mat")
    labels = load_mat(psse_dir / "V_magnitudes_angles.mat")

    Pij_stored = meas[:n_check, :n_branches]
    Qij_stored = meas[:n_check, n_branches:n_branches * 2]
    Vm = labels[:n_check, :n_buses]
    Va = labels[:n_check, n_buses:]

    ys = 1.0 / (r + 1j * x)
    gs, bs = ys.real, ys.imag
    bc = b / 2.0
    tap = ratio

    Vi = Vm[:, fbus]
    Vj = Vm[:, tbus]
    theta = Va[:, fbus] - Va[:, tbus]

    Pij_calc = (Vi / tap) ** 2 * gs - (Vi / tap) * Vj * (gs * np.cos(theta) + bs * np.sin(theta))
    Qij_calc = -(Vi / tap) ** 2 * (bs + bc) + (Vi / tap) * Vj * (bs * np.cos(theta) - gs * np.sin(theta))

    p_err = np.abs(Pij_calc - Pij_stored)
    q_err = np.abs(Qij_calc - Qij_stored)

    p_rel = p_err.mean() / np.abs(Pij_stored).max() * 100
    q_rel = q_err.mean() / np.abs(Qij_stored).max() * 100

    if p_rel > 0.1:
        issues.append(f"AC Pij relative error {p_rel:.4f}% exceeds 0.1% threshold")
    if q_rel > 0.1:
        issues.append(f"AC Qij relative error {q_rel:.4f}% exceeds 0.1% threshold")

    return issues, p_rel, q_rel


def check_gefcom_lineage(psse_dir: Path, gefcom_csv: Path, case: dict) -> tuple[list[str], dict]:
    """
    Verify load scale factors in the dataset match the GEFCom2012 total zone load
    distribution after factor-2 subsampling.
    """
    issues = []

    # ── extract per-sample load scale from dataset (using pure load buses) ──
    gen_buses = set(case["gen"][:, 0].astype(int))
    pure_load_indices = [
        i for i in range(case["bus"].shape[0])
        if case["bus"][i, 2] > 0 and int(case["bus"][i, 0]) not in gen_buses
    ]
    pd_base_pu = case["bus"][pure_load_indices, 2] / case["baseMVA"]

    inj = sio.loadmat(str(psse_dir / "Pi_Qi_injections.mat"))
    Pi  = inj["data"][:, pure_load_indices]
    scale = (-Pi / pd_base_pu).mean(axis=1)   # shape (N_samples,)

    # ── load and subsample GEFCom total zone load ──
    gefcom_total = load_gefcom_total_load(gefcom_csv)
    gefcom_sub   = gefcom_total[::2]           # factor-2 subsampling

    n_ds  = len(scale)
    n_gef = len(gefcom_sub)
    dropped = n_gef - n_ds

    if dropped < 0:
        issues.append(f"Dataset ({n_ds}) larger than GEFCom subsampled ({n_gef}); "
                      "cannot be a subset")
        return issues, {}

    # ── distribution comparison at key percentiles ──
    gefcom_norm = gefcom_sub / gefcom_sub.mean() * scale.mean()
    pcts = [5, 25, 50, 75, 95]
    gef_pcts = np.percentile(gefcom_norm, pcts)
    ds_pcts  = np.percentile(scale,       pcts)
    max_pct_err = np.abs(gef_pcts - ds_pcts).max() / ds_pcts.mean() * 100

    if max_pct_err > 10.0:
        issues.append(f"GEFCom/dataset load distribution diverges by {max_pct_err:.1f}% "
                      "(threshold 10%)")

    # ── temporal autocorrelation at lag 1 ──
    ac_ds  = np.corrcoef(scale[:-1],     scale[1:])[0, 1]
    ac_gef = np.corrcoef(gefcom_sub[:-1], gefcom_sub[1:])[0, 1]
    lag1_diff = abs(ac_ds - ac_gef)
    if lag1_diff > 0.05:
        issues.append(f"Lag-1 autocorrelation differs by {lag1_diff:.4f} (threshold 0.05)")

    stats = {
        "n_dataset":        n_ds,
        "n_gefcom_sub":     n_gef,
        "n_dropped":        dropped,
        "scale_min":        scale.min(),
        "scale_max":        scale.max(),
        "scale_mean":       scale.mean(),
        "max_pct_err":      max_pct_err,
        "ac_ds_lag1":       ac_ds,
        "ac_gef_lag1":      ac_gef,
        "pct_labels":       pcts,
        "gef_pcts":         gef_pcts.tolist(),
        "ds_pcts":          ds_pcts.tolist(),
    }
    return issues, stats


# ── main ───────────────────────────────────────────────────────────────────────

def run(repo_root: Path) -> int:
    paths = resolve_paths(repo_root)
    psse_dir    = paths["psse_dir"]
    gefcom_csv  = paths["gefcom_load"]

    for p in [psse_dir, gefcom_csv]:
        if not Path(p).exists():
            print(f"ERROR: path not found: {p}", file=sys.stderr)
            return 1

    case = case118()
    n_buses    = case["bus"].shape[0]
    n_branches = case["branch"].shape[0]
    all_issues = []

    # ── 1. dimensions ──
    print("[ 1/5 ] Checking measurement/label dimensions ...")
    issues = check_system_dimensions(psse_dir, case)
    all_issues.extend(issues)
    if not issues:
        meas   = load_mat(psse_dir / "Pij_Qij_Vi.mat")
        n_samples = meas.shape[0]
        print(f"        OK — {n_samples} samples, {n_branches * 2 + n_buses} measurements, "
              f"{n_buses * 2} labels")

    # ── 2. slack bus ──
    print("[ 2/5 ] Checking slack bus (Bus 69) is constant ...")
    issues = check_slack_bus(psse_dir, case)
    all_issues.extend(issues)
    if not issues:
        print(f"        OK — vm=1.035 pu, va=pi/6 rad (30 deg) constant across all samples")

    # ── 3. Vi == Vmag ──
    print("[ 3/5 ] Checking Vi (measurements) == Vmag (labels) ...")
    issues = check_vi_equals_vmag(psse_dir, case)
    all_issues.extend(issues)
    if not issues:
        print(f"        OK — exact match (max diff = 0.0)")

    # ── 4. AC power flow ──
    print("[ 4/5 ] Verifying AC power flow equations (first 1000 samples) ...")
    issues, p_rel, q_rel = check_ac_power_flow(psse_dir, case)
    all_issues.extend(issues)
    if not issues:
        print(f"        OK — Pij rel err={p_rel:.4f}%, Qij rel err={q_rel:.4f}%")

    # ── 5. GEFCom lineage ──
    print("[ 5/5 ] Verifying GEFCom2012 lineage ...")
    issues, stats = check_gefcom_lineage(psse_dir, gefcom_csv, case)
    all_issues.extend(issues)
    if not issues and stats:
        print(f"        OK — dataset has {stats['n_dataset']} samples "
              f"({stats['n_gefcom_sub']} GEFCom/2 - {stats['n_dropped']} dropped)")
        print(f"        Load scale: [{stats['scale_min']:.3f}, {stats['scale_max']:.3f}], "
              f"mean={stats['scale_mean']:.3f}")
        print(f"        Distribution max pct-err={stats['max_pct_err']:.2f}%  "
              f"Lag-1 autocorr: dataset={stats['ac_ds_lag1']:.4f}, "
              f"GEFCom={stats['ac_gef_lag1']:.4f}")

    # ── summary ──
    print()
    if all_issues:
        print(f"FAILED — {len(all_issues)} issue(s):")
        for iss in all_issues:
            print(f"  • {iss}")
        return 1
    else:
        print("PASSED — all checks passed.")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[2],
                        help="Path to repository root (default: two levels up from this file)")
    args = parser.parse_args()
    sys.exit(run(args.repo_root))
