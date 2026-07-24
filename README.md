# IEEE 118-bus Transient Stability Dataset

End-to-end pipeline producing transient stability datasets for the IEEE 118-bus system: GEFCom2012 load profiles → PSSE-via-DNNs operating points → PowerWorld base case → time-domain simulations.

The PowerWorld case is a corrected variant of the **KIOS modified IEEE 118-bus dynamic test system**. The operating-point sampling reproduces the methodology of Zhang, Wang & Giannakis ([arXiv:1811.06146](https://arxiv.org/abs/1811.06146)). See [Attribution](#attribution).

## Quick Start

Python 3.10 is the supported reproducibility baseline. GitHub contains the
pipeline, tests, and checksummed manifests; dataset payloads are obtained from
the associated Zenodo dataset version:

```sh
git clone https://github.com/0xSoliski/dataset-conversion-transients-powerworld.git
cd dataset-conversion-transients-powerworld
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

After the Zenodo payload has been placed at the paths recorded in
`datasets/release-manifest.json`, verify it and convert one export to a separate
output directory:

```sh
.venv/bin/python tools/build_scenario_manifest.py --check
.venv/bin/python tools/build_release_manifest.py --check
.venv/bin/python tools/powerworld_to_dataset.py \
  datasets/powerworld-ieee118/transient-simulations/gen26_shutdown/raw_export.xlsx \
  output/gen26_shutdown/dataset
```

On Windows, replace `.venv/bin/python` with
`.\.venv\Scripts\python.exe`. PowerWorld Simulator is required only to create
new transient exports; it is not required to reproduce conversion of the
tracked exports.

## Reproduction Scope

The repository intentionally tracks source code, provenance metadata, and
checksummed manifests only. The source datasets and PowerWorld exports needed
to verify lineage and regenerate the four published scenarios are dataset
payloads hosted by Zenodo. GitHub does not track datasets, model weights,
virtual environments, caches, validation logs, or generated output.

## Data Publication Boundary

The publication layout is a clean code-and-manifest GitHub history with
complete, versioned data payloads stored in the shared Zenodo dataset
collection. No Git LFS objects are used.

`datasets/release-manifest.json` inventories every current dataset payload with
its byte size, SHA-256 digest, provenance class, redistribution status, and
target storage. Rebuild or verify it with:

```sh
python tools/build_release_manifest.py
python tools/build_release_manifest.py --check
```

[`DATASET_SOURCE.json`](DATASET_SOURCE.json) is the machine-readable pointer
that all participating GitHub repositories share.

The manifest remains the authoritative inventory while the dataset-only Zenodo
version is prepared. Its checksums can be regenerated only from a complete
local copy of the Zenodo payload.

Zenodo must contain dataset payloads only. GitHub source archives, Python or
MATLAB code, workflows, repository metadata, and model implementations are
excluded. GitHub-to-Zenodo repository integration is intentionally not used.
`tools/build_release_manifest.py` rejects non-data files, including code hidden
inside ZIP payloads, and assigns each approved dataset file a unique Zenodo key.

Rights-cleared dataset payloads use CC BY 4.0, which permits reuse and
adaptation with attribution. The exact scope, attribution text, and third-party
exclusions are documented in [`DATA_LICENSE.md`](DATA_LICENSE.md). A collection
license never overrides an upstream provider's rights; files without verified
redistribution permission are not included in the public upload package.

The existing Zenodo concept DOI
[`10.5281/zenodo.20744597`](https://doi.org/10.5281/zenodo.20744597) is
preserved for reuse as the shared PINN dataset collection. Its `v0.1.0` and
`v0.1.1` archives contain the same 49 files under `datasets/` as this local
repository: 46 data payloads or non-code sidecars plus three source files. The
new dataset-only manifest excludes those source files, and the current tree
adds only release/provenance manifests. No deletion or deprecation is planned.

The dataset-only `v0.2.0` draft is Zenodo record
[`21533592`](https://zenodo.org/records/21533592), with reserved version DOI
`10.5281/zenodo.21533592`. It is configured as a public Dataset under CC BY
4.0 and currently contains zero files: no blocked payload and no source code
has been uploaded.

The comparison evidence, tagged commits, archive checksums, and exact reuse
decision are recorded in [`ZENODO_RECORDS.md`](ZENODO_RECORDS.md).

Those two historical versions remain restricted because their immutable ZIP
files also contain source code and repository metadata. After redistribution
rights are verified, populate the dataset-only `v0.2.0` draft with files that
match `datasets/shared-release-manifest.json`, independently verify them, and
publish that version. Do not make the code-containing versions public again or
treat them as runtime dependencies.

Generated FDIA and IEEE-14 datasets use named collections inside the same
Zenodo record family. Their different producers and provenance chains are
captured by collection IDs, checksums, and generation manifests. See
[`DATASET_COLLECTIONS.md`](DATASET_COLLECTIONS.md) for the repository mapping.
Prepare and validate upload packages and metadata locally first. Creating the
draft and reserving its DOI are complete. Publishing remains blocked until the
third-party redistribution gates pass and the upload package independently
matches the manifest.

## Layout

```
datasets/
├── gefcom2012/original/                       upstream load data (Tao Hong, GEFCom2012)
├── psse-via-dnns/
│   ├── original/pypower-ieee118/              published PSSE benchmark (.mat, 18 528 samples)
│   └── derived/powerworld-static/generate.py  PSSE sample → PowerWorld import workbooks
└── powerworld-ieee118/
    ├── case/                                  IEEE-118-Bus.pwb/.pwd (transient dynamics + bus-19 fault contingency embedded)
    ├── reference/                             KIOS reference Gen sheet (input to generate.py)
    ├── import-files/                          generated workbooks to paste into the .pwb
    ├── transient-simulations/                 simulation outputs (.csv, .mat, .xlsx)
    │   ├── three-phase-fault-bus19/
    │   ├── load-increase-20-to-27/
    │   ├── gen26_shutdown/
    │   └── gen59_shutdown/
    └── matlab/                                PowerWorld export → dataset converter
tools/
├── psse-verification/verify.py                checks PSSE lineage against GEFCom2012
└── powerworld-paste-check/                    Bus/Load/Gen and Ybus consistency checks
```

## The dataset

Each `transient-simulations/*/dataset.mat` contains time-series of operating-point variables for all 118 buses:

| Variable | Shape | Units |
|---|---|---|
| `features` | `T × 236` | columns 1–118 net Pi / 100 (pu), 119–236 net Qi / 100 (pu) |
| `labels`   | `T × 236` | columns 1–118 voltage magnitude Vm (pu), 119–236 voltage angle Va (rad) |

`dataset.csv` concatenates `[features  labels]` in the same column order. `raw_export.xlsx` is the source PowerWorld `TSTimePointResult` sheet.
The versioned cross-repository schema is defined in [DATASET_CONTRACT.md](DATASET_CONTRACT.md).

Scenarios:
- **three-phase-fault-bus19** — 3-phase impedance fault at bus 19, applied at *t*=1.0 s, cleared at *t*=1.1 s.
- **load-increase-20-to-27** — coordinated load step from load bus 20 to 27.
- **gen26_shutdown** — generator at bus 26 tripped offline (validation dataset).
- **gen59_shutdown** — generator at bus 59 tripped offline (validation dataset).

Load in Python (`scipy.io.loadmat`) or MATLAB (`load`).

## Pipeline

1. **GEFCom2012 → PSSE-via-DNNs**: sum all 20 zones, subsample by 2, normalize, run AC power flow on PYPOWER `case118`, drop non-converged → 18 528 samples. Verified against the AC power flow equations to 0.001 % relative error by `tools/psse-verification/verify.py`.
2. **PSSE sample → PowerWorld imports**: `generate.py` selects one operating-point sample (default 17103, scale ≈ 0.87) and writes five paste-ready workbooks. Transient dynamics and the bus-19 fault contingency are already embedded in the bundled `.pwb`.
3. **PowerWorld transient run**: paste the workbooks into `case/IEEE-118-Bus.pwb`, run the desired transient scenario, export the time-point sheet, then convert it with the Python CLI below. The MATLAB implementation remains available as a reference.

## Bridging GEFCom2012 to the IEEE 118-bus case

The upstream GEFCom2012 data is 20 zones of hourly load values in competition-defined units — it has no electrical model attached. The IEEE 118-bus case is a static AC network whose nominal total load is 4 242 MW across 91 load buses. They are reconciled in four steps (methodology after Zhang et al.):

1. **Aggregate** — sum all 20 GEFCom zones per hour, giving a single scalar load time series (38 070 hourly points where every zone reports).
2. **Subsample** — keep every other hour → 19 035 steps.
3. **Normalize to a per-unit multiplier** — divide each step's aggregate by a reference value chosen so the resulting multiplier lands the case in a sensible operating regime (mean ≈ 0.47, range 0.24–0.87 of the IEEE 118 base load). This collapses unit mismatch and time-zone differences into a single dimensionless scalar.
4. **Apply uniformly** — at each step, scale all 91 IEEE 118-bus loads by that multiplier (the base case's relative spatial load distribution is preserved; only total magnitude moves). Solve AC power flow on PYPOWER `case118` with the slack bus at 69 absorbing the residual. Samples that do not converge are dropped (507 of 19 035), leaving 18 528 retained samples.

The PowerWorld base case adds dynamic generator models, exciters, and governors on top of one chosen sample (default 17103). Because the operating point and the dynamics are decoupled (the `.pwb` defines generator MW/Mvar setpoints, voltages, and angles independently of the dynamic state), any of the 18 528 samples can be pasted in without re-tuning the dynamics. `tools/psse-verification/verify.py` round-trips the GEFCom multiplier through AC power flow and confirms agreement with the published PSSE-via-DNNs labels to 0.001 % relative error.

**Sample selection for transient simulations.** All 18 528 samples are AC-valid by construction. Transient quality depends on how far the chosen sample deviates from the KIOS reference dispatch: `generate.py` closes that gap with signed static equivalent injections, but large equivalents (low-load samples, scale ≲ 0.5) move the operating point far from the regime the dynamic models were tuned for and can produce unphysical transient trajectories. Samples in the upper load-scale range (≳ 0.5, ideally ≳ 0.7) produce smaller equivalents and better-behaved transient initialization. Sample 17103 (scale ≈ 0.87) was selected as the default because it sits near the top of the range with a positive Bus 69 slack injection, minimising the equivalent injection magnitude and matching the reference dispatch closely.

## Reproduce

On POSIX:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

.venv/bin/python tools/psse-verification/verify.py
.venv/bin/python datasets/psse-via-dnns/derived/powerworld-static/generate.py

.venv/bin/python tools/powerworld_to_dataset.py raw_export.xlsx dataset
```

On Windows PowerShell:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe tools\psse-verification\verify.py
.\.venv\Scripts\python.exe datasets\psse-via-dnns\derived\powerworld-static\generate.py

.\.venv\Scripts\python.exe tools\powerworld_to_dataset.py raw_export.xlsx dataset
```

To validate a freshly pasted PowerWorld case before running TS:

```sh
.venv/Scripts/python tools/powerworld-paste-check/compare_ybus.py \
    --powerworld-ybus datasets/powerworld-ieee118/import-files/ybus.xlsx

.venv/Scripts/python tools/powerworld-paste-check/compare_pasted_state.py \
    --bus-export  datasets/powerworld-ieee118/import-files/buses.xlsx \
    --load-export datasets/powerworld-ieee118/import-files/demand_loads.xlsx \
    --gen-export  datasets/powerworld-ieee118/import-files/generators.xlsx
```

The Python converter validates the worksheet name, every ordered bus header,
numeric completeness, and finite values before writing `features` and `labels`.
By default it discards the first two numeric time points to remain numerically
compatible with the historical MATLAB converter. Pass `--skip-data-rows 0` for
new exports when those initial points should be retained.

Run the automated validation with:

```sh
python -m pip install pytest
python -m pytest -q
python tools/build_scenario_manifest.py --check
```

The scenario manifest at
`datasets/powerworld-ieee118/transient-simulations/manifest.json` records the
schema and SHA-256 digest of every source export and generated dataset.

## Attribution

- **PowerWorld case** — KIOS modified IEEE 118-bus dynamic test system (KIOS Research Center, University of Cyprus, <https://www.kios.ucy.ac.cy/testsystems/>). Cite: P. Demetriou, M. Asprou, J. Quirós-Tortós, E. Kyriakides, "Dynamic IEEE Test Systems for Transient Analysis," *IEEE Systems Journal*, vol. 11, no. 4, pp. 2108–2117, Dec. 2017. The bundled `.pwb` includes branch-admittance corrections so the topology matches PYPOWER `case118`; the dynamic models (GENROU, IEEET1, BPA_GG) and bus-19 three-phase fault contingency are from the KIOS release.
- **Operating-point methodology** — L. Zhang, G. Wang, G. B. Giannakis, "Real-time Power System State Estimation and Forecasting via Deep Neural Networks," [arXiv:1811.06146](https://arxiv.org/abs/1811.06146). Load-scaling and AC-power-flow sampling reproduce the [PSSE-via-DNNs](https://github.com/LiangZhangUMN/PSSE-via-DNNs) benchmark.
- **Upstream load data** — GEFCom2012 (Tao Hong et al.), <https://blog.drhongtao.com/2016/07/gefcom2012-load-forecasting-data.html>.
- **Base topology** — IEEE 118-bus test case, [ICSEG IEEE 118 Bus System](https://icseg.iti.illinois.edu/ieee-118-bus-system/).

## License

Project code (Python scripts, MATLAB converters, README) is released under the
MIT License — see [LICENSE](LICENSE). Bundled third-party content is not covered
by that grant. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); its
redistribution checklist is a release gate and must be resolved before another
public release.
