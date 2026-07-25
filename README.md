# dataset-conversion-transients-powerworld

End-to-end pipeline producing transient stability datasets for the IEEE 118-bus
system: GEFCom2012 load profiles → operating points via AC power flow →
PowerWorld base case → time-domain simulations.

The PowerWorld case is a corrected variant of the **KIOS modified IEEE 118-bus
dynamic test system**. The operating-point sampling reproduces the methodology of
Zhang, Wang & Giannakis ([arXiv:1811.06146](https://arxiv.org/abs/1811.06146)).
See [Citation](#citation) for the full attribution chain.

Source code lives here; the dataset payloads live on Zenodo. This repository
tracks the pipeline and its tests only.

## Paper

This is the dataset-generation component of the PINN/FDIA publication family. It
produces the base and transient/fault collections consumed by the model
repositories:
[`pinns-models-tii`](https://github.com/0xSoliski/pinns-models-tii),
[`pinns-models-csr`](https://github.com/0xSoliski/pinns-models-csr),
[`pinns-models-fdia`](https://github.com/0xSoliski/pinns-models-fdia),
[`pinns-models-fdia-ablation-dynamic`](https://github.com/0xSoliski/pinns-models-fdia-ablation-dynamic),
and
[`pinns-models-fdia-journal-ablation-faults`](https://github.com/0xSoliski/pinns-models-fdia-journal-ablation-faults),
plus the adversarial scenarios built by
[`fdia-construction-pipeline`](https://github.com/0xSoliski/fdia-construction-pipeline).

### Pipeline

1. **GEFCom2012 → operating points** — sum all 20 zones, subsample by 2,
   normalize, run AC power flow on PYPOWER `case118`, drop non-converged →
   18,528 samples. Verified against the AC power-flow equations to 0.001 %
   relative error by `tools/psse-verification/verify.py`.
2. **Sample → PowerWorld imports** — `generate.py` selects one operating-point
   sample (default 17103, scale ≈ 0.87) and writes five paste-ready workbooks.
   Transient dynamics and the bus-19 fault contingency are already embedded in
   the bundled `.pwb`.
3. **PowerWorld transient run** — paste the workbooks into
   `case/IEEE-118-Bus.pwb`, run the desired scenario, export the time-point
   sheet, then convert it with the Python CLI. The MATLAB implementation remains
   available as a reference.

### Bridging GEFCom2012 to the IEEE 118-bus case

The upstream GEFCom2012 data is 20 zones of hourly load values in
competition-defined units — it has no electrical model attached. The IEEE 118-bus
case is a static AC network whose nominal total load is 4,242 MW across 91 load
buses. They are reconciled in four steps (methodology after Zhang et al.):

1. **Aggregate** — sum all 20 GEFCom zones per hour, giving a single scalar load
   time series (38,070 hourly points where every zone reports).
2. **Subsample** — keep every other hour → 19,035 steps.
3. **Normalize to a per-unit multiplier** — divide each step's aggregate by a
   reference value chosen so the resulting multiplier lands the case in a sensible
   operating regime (mean ≈ 0.47, range 0.24–0.87 of the IEEE 118 base load).
   This collapses unit mismatch and time-zone differences into a single
   dimensionless scalar.
4. **Apply uniformly** — at each step, scale all 91 IEEE 118-bus loads by that
   multiplier, preserving the base case's relative spatial load distribution and
   moving only total magnitude. Solve AC power flow on PYPOWER `case118` with the
   slack bus at 69 absorbing the residual. Non-converged samples are dropped
   (507 of 19,035), leaving 18,528 retained.

The PowerWorld base case adds dynamic generator models, exciters, and governors
on top of one chosen sample. Because the operating point and the dynamics are
decoupled — the `.pwb` defines generator MW/Mvar setpoints, voltages, and angles
independently of the dynamic state — any of the 18,528 samples can be pasted in
without re-tuning the dynamics.

**Sample selection for transient simulations.** All 18,528 samples are AC-valid
by construction. Transient quality depends on how far the chosen sample deviates
from the KIOS reference dispatch: `generate.py` closes that gap with signed
static equivalent injections, but large equivalents (low-load samples, scale
≲ 0.5) move the operating point far from the regime the dynamic models were tuned
for and can produce unphysical transient trajectories. Samples in the upper
load-scale range (≳ 0.5, ideally ≳ 0.7) produce smaller equivalents and
better-behaved transient initialization. Sample 17103 (scale ≈ 0.87) is the
default because it sits near the top of the range with a positive bus-69 slack
injection, minimising the equivalent injection magnitude and matching the
reference dispatch closely.

## Data

The datasets are on Zenodo:
[10.5281/zenodo.20744597](https://doi.org/10.5281/zenodo.20744597).

Download them into `datasets/`. That tree is local only and is not committed.

### The dataset

Each `transient-simulations/*/dataset.mat` contains time series of
operating-point variables for all 118 buses:

| Variable | Shape | Units |
| --- | --- | --- |
| `features` | `T × 236` | columns 1–118 net Pi / 100 (pu), 119–236 net Qi / 100 (pu) |
| `labels` | `T × 236` | columns 1–118 voltage magnitude Vm (pu), 119–236 voltage angle Va (rad) |

`dataset.csv` concatenates `[features labels]` in the same column order;
`raw_export.xlsx` is the source PowerWorld `TSTimePointResult` sheet. Load with
`scipy.io.loadmat` in Python or `load` in MATLAB.

Scenarios:

- **three-phase-fault-bus19** — 3-phase impedance fault at bus 19, applied at
  *t* = 1.0 s, cleared at *t* = 1.1 s
- **load-increase-20-to-27** — coordinated load step from load bus 20 to 27
- **gen26_shutdown** — generator at bus 26 tripped offline (validation dataset)
- **gen59_shutdown** — generator at bus 59 tripped offline (validation dataset)

The Zenodo record holds the generated datasets under CC BY 4.0, which allows
reuse and adaptation with attribution — see [Citation](#citation). The raw
GEFCom2012 load data and the KIOS PowerWorld case file are inputs obtained from
their original providers and are not redistributed here; get them from the
sources listed under Citation.

## Installation

The supported baseline is Linux, Python 3.10.

```bash
python -m pip install -r requirements.txt
```

PowerWorld Simulator is required only to create *new* transient exports; it is
not needed to reproduce conversion of the tracked exports.

## Reproducing the results

The test suite validates the converter without any dataset present:

```bash
python -m pytest -q
```

Verify the lineage and regenerate the PowerWorld import workbooks:

```bash
python tools/psse-verification/verify.py
```

```bash
python datasets/psse-via-dnns/derived/powerworld-static/generate.py
```

Convert a PowerWorld export to a dataset:

```bash
python tools/powerworld_to_dataset.py datasets/powerworld-ieee118/transient-simulations/gen26_shutdown/raw_export.xlsx output/gen26_shutdown/dataset
```

The converter validates the worksheet name, every ordered bus header, numeric
completeness, and finite values before writing `features` and `labels`. By
default it discards the first two numeric time points to stay numerically
compatible with the historical MATLAB converter; pass `--skip-data-rows 0` for
new exports when those points should be retained.

Validate a freshly pasted PowerWorld case before running a transient study:

```bash
python tools/powerworld-paste-check/compare_ybus.py --powerworld-ybus datasets/powerworld-ieee118/import-files/ybus.xlsx
```

```bash
python tools/powerworld-paste-check/compare_pasted_state.py --bus-export datasets/powerworld-ieee118/import-files/buses.xlsx --load-export datasets/powerworld-ieee118/import-files/demand_loads.xlsx --gen-export datasets/powerworld-ieee118/import-files/generators.xlsx
```

## Repository layout

```text
datasets/
├── gefcom2012/original/                       upstream load data (Tao Hong, GEFCom2012)
├── psse-via-dnns/
│   ├── original/pypower-ieee118/              base operating-point set (.mat, 18,528 samples)
│   └── derived/powerworld-static/generate.py  sample → PowerWorld import workbooks
└── powerworld-ieee118/
    ├── case/                                  IEEE-118-Bus.pwb/.pwd (dynamics + bus-19 fault embedded)
    ├── reference/                             KIOS reference Gen sheet (input to generate.py)
    ├── import-files/                          generated workbooks to paste into the .pwb
    ├── transient-simulations/                 simulation outputs (.csv, .mat, .xlsx)
    └── matlab/                                PowerWorld export → dataset converter
tools/
├── psse-verification/verify.py                checks lineage against GEFCom2012
└── powerworld-paste-check/                    Bus/Load/Gen and Ybus consistency checks
tests/                                         CPU suite
```

## Citation

Cite this repository for the dataset-generation pipeline and the Zenodo record
for the data. [`CITATION.cff`](CITATION.cff) carries machine-readable metadata
for the software.

Reuse under CC BY 4.0 requires attribution. The upstream chain is:

- **PowerWorld case** — KIOS modified IEEE 118-bus dynamic test system (KIOS
  Research Center, University of Cyprus,
  <https://www.kios.ucy.ac.cy/testsystems/>). Cite: P. Demetriou, M. Asprou,
  J. Quirós-Tortós, and E. Kyriakides, "Dynamic IEEE Test Systems for Transient
  Analysis," *IEEE Systems Journal*, vol. 11, no. 4, pp. 2108–2117, Dec. 2017.
  The bundled `.pwb` includes branch-admittance corrections so the topology
  matches PYPOWER `case118`; the dynamic models (GENROU, IEEET1, BPA_GG) and the
  bus-19 three-phase fault contingency are from the KIOS release.
- **Operating-point methodology** — L. Zhang, G. Wang, and G. B. Giannakis,
  "Real-time Power System State Estimation and Forecasting via Deep Neural
  Networks," [arXiv:1811.06146](https://arxiv.org/abs/1811.06146). The
  load-scaling and AC-power-flow sampling reproduce the
  [PSSE-via-DNNs](https://github.com/LiangZhangUMN/PSSE-via-DNNs) benchmark
  methodology.
- **Upstream load data** — GEFCom2012 (Tao Hong et al.),
  <https://blog.drhongtao.com/2016/07/gefcom2012-load-forecasting-data.html>.
  Described by T. Hong, P. Pinson, and S. Fan, "Global Energy Forecasting
  Competition 2012," *International Journal of Forecasting*, doi:
  [10.1016/j.ijforecast.2013.07.001](https://doi.org/10.1016/j.ijforecast.2013.07.001).
- **Base topology** — IEEE 118-bus test case,
  [ICSEG IEEE 118 Bus System](https://icseg.iti.illinois.edu/ieee-118-bus-system/).

## License

Code in this repository (Python scripts, MATLAB converters, this README) is
released under the MIT License — see [`LICENSE`](LICENSE). The datasets on Zenodo
are licensed CC BY 4.0 and require attribution — see
[Citation](#citation) for the credits to include.
