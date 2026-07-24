# Shared PINN Dataset Collection

All PINN software repositories publish code, configuration, manifests, and
small synthetic test fixtures on GitHub. Real training, evaluation, attack,
fault, and transient datasets belong in one versioned Zenodo dataset
collection. Git LFS is not used.

The preserved collection concept DOI is
[`10.5281/zenodo.20744597`](https://doi.org/10.5281/zenodo.20744597).
Every consuming repository records this concept DOI in `DATASET_SOURCE.json`.
After a dataset-only version is published, each repository must also pin that
version's exact DOI and record ID before a public release.

## Collection layout

| Collection ID | Contents |
| --- | --- |
| `ieee118-base-state-estimation` | Canonical `combined_dataset.mat` and explicitly documented format conversions |
| `ieee118-transient-and-fault` | PowerWorld-derived IEEE-118 fault, generator, and load-change scenarios |
| `ieee118-fdia` | Generated IEEE-118 FDIA training and evaluation datasets |
| `ieee14-base-state-estimation` | Canonical IEEE-14 steady-state data and required grid matrices |
| `ieee14-transient-and-fault` | IEEE-14 generator, load, fault, and transient scenarios |
| `ieee14-fdia` | IEEE-14 data-manipulation and FDIA scenarios |

The same immutable Zenodo version may contain all six collections. Different
producers and provenance chains are represented by collection IDs, file
metadata, checksums, and generation manifests rather than by creating separate
DOIs.

The checked-in `datasets/release-manifest.json` currently inventories only the
IEEE-118 base and transient/fault collections produced by this repository. It
is not yet the complete upload inventory. Before publication, the exact
IEEE-14 and FDIA inventories from their producing repositories must be merged,
deduplicated by SHA-256, and checked again for source-code extensions.

## Repository mapping

| GitHub repository | Dataset collections |
| --- | --- |
| `dataset-conversion-transients-powerworld` | Produces the upstream IEEE-118 base and PowerWorld transient/fault exports; curates the shared record inventory |
| `fdia-construction-pipeline` | Consumes `ieee118-base-state-estimation`; produces `ieee118-fdia` |
| `pinns-models-fdia` | Consumes both IEEE-14 and IEEE-118 base, transient/fault, and FDIA collections |
| `pinns-models-fdia-ablation-dynamic` | Consumes all three IEEE-118 collections; fault/contingency inputs are supplied through the fault-ablation inventory |
| `pinns-models-fdia-ablation-faults` | Consumes IEEE-118 base data and owns the paper-facing four-scenario `ieee118-transient-and-fault` inventory and verification |
| `pinns-models-csr` | Consumes IEEE-14 base/FDIA data; preserves IEEE-118 base/FDIA dependencies for its archived evaluator |
| `pinns-models-tii` | Consumes all six collections |

Production provenance and paper-facing stewardship are intentionally distinct.
`dataset-conversion-transients-powerworld` records how the PowerWorld exports
were converted. `pinns-models-fdia-ablation-faults` defines and verifies the
four-scenario subset used by the fault-ablation experiment. The final GitHub
history of the latter contains the inventory and checksums, while the `.mat`
payloads are served only by the shared Zenodo dataset version.

## Publication rules

- Zenodo files are datasets only. Source code, notebooks, repository archives,
  model implementations, environments, and generated GitHub source archives
  are forbidden.
- Derived datasets used for published metrics are deposited even when they can
  be regenerated, so an exact paper input remains available. Their generation
  manifest must identify the source dataset SHA-256 and producing Git commit.
- Consumers pin an exact version DOI for reproducibility. The concept DOI is
  used only as the stable collection identity and while the dataset-only
  version is still pending.
- GitHub histories are rebuilt without real dataset payloads. Small synthetic
  fixtures may remain solely for tests.
- No dataset-only version is published until redistribution and simulator
  licensing gates are resolved.
