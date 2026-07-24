# PowerWorld Paste Checks

Sanity checks for a freshly pasted PowerWorld case before running transient stability.

**Bus/Load/Gen state** — confirms pasted voltages, angles, load rows, equivalent injections, and generator dispatch match the generated targets:

```sh
.venv/Scripts/python tools/powerworld-paste-check/compare_pasted_state.py \
  --bus-export <bus.xlsx> --load-export <loads.xlsx> --gen-export <gens.xlsx>
```

**Ybus** — confirms the exported 118×118 admittance matrix matches the PYPOWER `case118` Ybus:

```sh
.venv/Scripts/python tools/powerworld-paste-check/compare_ybus.py \
  --powerworld-ybus <ybus.xlsx>
```
