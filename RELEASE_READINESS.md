# Release Readiness

- [ ] CI and PSSE/GEFCom verification pass from a clean checkout.
- [ ] The deterministic conversion smoke workflow passes on Linux/Python 3.10
      in CI.
- [x] Python and MATLAB converters remain numerically compatible for all four
      preserved PowerWorld scenarios.
- [x] The scenario manifest is current.
- [x] The Zenodo-oriented release manifest is current and every recorded SHA-256
      matches the proposed dataset payload.
- [x] The 49 files under `datasets/` in Zenodo `v0.1.0` and `v0.1.1` are
      identical to one another and to the current local tree: 46 data files
      plus three source files excluded from the dataset-only release; only two
      local manifests were added later.
- [x] The preserved concept DOI `10.5281/zenodo.20744597` has a dataset-only
      `v0.2.0` draft, record `21533592`, with reserved DOI
      `10.5281/zenodo.21533592`.
- [x] The release inventory rejects code and repository archives; GitHub-Zenodo
      repository integration is disabled.
- [x] The historical code-containing versions are preserved, restricted, and
      are not deletion or deprecation targets.
- [ ] Every third-party publication gate in `THIRD_PARTY_NOTICES.md` is resolved.
- [ ] Cross-repository model evaluation accepts all four exported datasets.
- [x] Every code repository pins the same exact reserved dataset version DOI
      and only selects the named collections it requires.
- [ ] A rights-approved dataset-only upload package and complete metadata have
      been built and validated locally before files are uploaded to the draft.
- [x] The public GitHub history has been replaced by a clean code-and-manifest
      history that does not distribute the large payloads.

Publication gate: this repository is already public and the dataset-only draft
has been authorized and created. Do not upload blocked files or publish the
draft until the third-party publication gates are resolved. Do not restore
public file access to the historical code-containing versions.
