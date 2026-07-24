# Dataset Contract v1

All cross-repository MATLAB datasets contain:

- `features`: two-dimensional numeric array with columns
  `[P_1..P_N, Q_1..Q_N]` in per unit on a 100 MVA base.
- `labels`: two-dimensional numeric array with columns
  `[V_1..V_N, theta_1..theta_N]`, with voltage in per unit and angle in radians.
- rows in `features` and `labels` correspond one-to-one.
- buses use ascending IEEE case order; attack-area metadata uses zero-based
  indices and must state that convention.

For IEEE 118-bus datasets, both arrays have 236 columns. Producers must reject
non-finite values and write provenance, scenario, source SHA-256, and schema
version metadata. Consumers must reject missing keys, mismatched rows, odd
feature widths, or a bus count inconsistent with the selected case.
