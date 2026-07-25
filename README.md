# dataset-conversion-transients-powerworld

Builds the IEEE 118-bus datasets used across the PINN state-estimation papers:
GEFCom2012 load profiles → operating points via AC power flow → PowerWorld base
case → time-domain transient simulations.

The PowerWorld case is a corrected variant of the KIOS modified IEEE 118-bus
dynamic test system. Operating-point sampling follows the methodology of Zhang,
Wang & Giannakis ([arXiv:1811.06146](https://arxiv.org/abs/1811.06146)).

## Paper

The datasets produced here are used by:

- S. Falas, M. Asprou, C. Konstantinou, and M. K. Michael, "Robust Power System
  State Estimation Using Physics-Informed Neural Networks," *IEEE Transactions on
  Industrial Informatics*, vol. 21, no. 10, pp. 8057–8067, 2025.
  doi: [10.1109/TII.2025.3582293](https://doi.org/10.1109/TII.2025.3582293)
- S. Falas, M. Asprou, and M. K. Michael, "Secure State Estimation Using
  Dynamically Weighted Physics-Informed Neural Networks Without Adversarial
  Training." Under review.

## Entry points and data

Install (Linux, Python 3.10):

```bash
python -m pip install -r requirements.txt
```

PowerWorld Simulator is only needed to create *new* transient exports, not to
convert existing ones.

The canonical IEEE-118 base dataset and four converted transient/fault
scenarios are tracked under `datasets/`. The complete historical archive is
available from [Zenodo v0.1.1](https://doi.org/10.5281/zenodo.20744819).
The raw GEFCom2012 load data and KIOS case remain with their original providers.

| Entry point | What it does |
| --- | --- |
| `tools/psse-verification/verify.py` | checks the operating points against AC power flow and the GEFCom2012 lineage |
| `datasets/psse-via-dnns/derived/powerworld-static/generate.py` | writes the five paste-ready PowerWorld import workbooks |
| `tools/powerworld_to_dataset.py` | converts a PowerWorld export to `features`/`labels` |
| `tools/powerworld-paste-check/` | Bus/Load/Gen and Ybus consistency checks |

Pipeline:

```bash
python tools/psse-verification/verify.py
```

```bash
python datasets/psse-via-dnns/derived/powerworld-static/generate.py
```

```bash
python tools/powerworld_to_dataset.py datasets/powerworld-ieee118/transient-simulations/gen26_shutdown/raw_export.xlsx output/gen26_shutdown/dataset
```

The converter validates the worksheet name, every ordered bus header, numeric
completeness, and finite values. It drops the first two numeric time points to
match the historical MATLAB converter; pass `--skip-data-rows 0` to keep them.

Each `dataset.mat` holds `features` (`T × 236`: net Pi/100 then Qi/100, pu) and
`labels` (`T × 236`: Vm in pu then Va in rad). Scenarios are
`three-phase-fault-bus19` (fault at *t* = 1.0 s, cleared at 1.1 s),
`load-increase-20-to-27`, `gen26_shutdown`, and `gen59_shutdown`.

## Tests

```bash
python -m pytest -q
```

Expect **2 passed, 4 skipped**. The skips need the Zenodo transient/fault data
present and state so; the rest validate the converter on synthetic input.

Expected results from a full run: `verify.py` reproduces the published operating
points to **0.001 % relative error**. The GEFCom2012 bridge aggregates all 20
zones, subsamples by 2 (19,035 steps), normalizes to a per-unit multiplier
(mean ≈ 0.47, range 0.24–0.87), scales all 91 loads, and solves AC power flow on
PYPOWER `case118` with the slack at bus 69 — dropping 507 non-converged steps for
**18,528 retained samples**. `generate.py` defaults to sample 17103
(scale ≈ 0.87), chosen because a high load scale keeps the static equivalent
injections small and the transient initialization well behaved.

## Citation

```bibtex
@article{falas2025tii,
  author  = {Falas, Solon and Asprou, Markos and Konstantinou, Charalambos and Michael, Maria K.},
  title   = {Robust Power System State Estimation Using Physics-Informed Neural Networks},
  journal = {IEEE Transactions on Industrial Informatics},
  year    = {2025},
  volume  = {21},
  number  = {10},
  pages   = {8057--8067},
  doi     = {10.1109/TII.2025.3582293}
}
```

Datasets are CC BY 4.0 and require attribution. Cite the Zenodo record and credit
the upstream sources:

- **KIOS dynamic IEEE test system** — P. Demetriou, M. Asprou, J. Quirós-Tortós,
  and E. Kyriakides, "Dynamic IEEE Test Systems for Transient Analysis," *IEEE
  Systems Journal*, vol. 11, no. 4, pp. 2108–2117, 2017.
  <https://www.kios.ucy.ac.cy/testsystems/>
- **Operating-point methodology** — L. Zhang, G. Wang, and G. B. Giannakis,
  "Real-time Power System State Estimation and Forecasting via Deep Neural
  Networks," [arXiv:1811.06146](https://arxiv.org/abs/1811.06146).
- **Load data** — GEFCom2012 (Tao Hong et al.); T. Hong, P. Pinson, and S. Fan,
  "Global Energy Forecasting Competition 2012," *International Journal of
  Forecasting*, doi:
  [10.1016/j.ijforecast.2013.07.001](https://doi.org/10.1016/j.ijforecast.2013.07.001).
- **Base topology** — IEEE 118-bus test case,
  [ICSEG](https://icseg.iti.illinois.edu/ieee-118-bus-system/).

Code is MIT licensed — see [`LICENSE`](LICENSE).
