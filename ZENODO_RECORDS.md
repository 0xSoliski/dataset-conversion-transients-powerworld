# Zenodo Record Equivalence

Verified on 2026-07-24 against the signed-in Zenodo records and local Git
history.

## Preserved record family

| Version | Zenodo DOI | Preserved backup commit | Archive MD5 | Files under `datasets/` |
| --- | --- | --- | --- | ---: |
| `v0.1.0` | [`10.5281/zenodo.20744598`](https://doi.org/10.5281/zenodo.20744598) | `d847d81f0d3b090c5ac74ea7025b01e62ce52e44` | `1820644a52af2dbe592fd4c4b0858ab1` | 49 |
| `v0.1.1` | [`10.5281/zenodo.20744819`](https://doi.org/10.5281/zenodo.20744819) | `d5fee07e5e1242d8fcd138463bc77b80d915e542` | `9ccfe763b53cb675de1a8823748da66d` | 49 |

The concept DOI for all versions is
[`10.5281/zenodo.20744597`](https://doi.org/10.5281/zenodo.20744597).

## Dataset-only draft

Zenodo record [`21533592`](https://zenodo.org/records/21533592) is the
dataset-only `v0.2.0` draft in this record family. Its reserved version DOI is
`10.5281/zenodo.21533592`. The draft is configured as:

- resource type: Dataset;
- file access: Public;
- license: CC BY 4.0 for rights-cleared files;
- files: zero, pending redistribution clearance.

The draft metadata explicitly excludes code, trained models, software
environments, and generated figures. The DOI is reserved but is not registered
until the record is published.

## Equivalence result

The `datasets/` Git tree object for both tagged versions is:

```text
9955d31c12f1fba66bc8f330dfa77be47cf15a3b
```

All 49 paths and blob IDs under `datasets/` are identical between the preserved
`v0.1.0` and `v0.1.1` backup commits and the private local preservation copy.
Of those files, 46 are data payloads or non-code data sidecars and three are
source files that must remain on GitHub:

```text
datasets/powerworld-ieee118/matlab/powerworld_to_dataset.m
datasets/powerworld-ieee118/matlab/ybus_converter.m
datasets/psse-via-dnns/derived/powerworld-static/generate.py
```

The dataset-only release manifest excludes those three source files. The
current repository adds only:

```text
datasets/powerworld-ieee118/transient-simulations/manifest.json
datasets/release-manifest.json
```

The 46 data payloads therefore must not be re-uploaded as a competing record
merely because the local migration added manifests.

## Reuse decision

The record family is preserved and is not a deletion or deprecation target.
The two published versions remain restricted because each immutable GitHub ZIP
also contains source code and repository metadata. They cannot be made the
canonical public dataset package without violating the dataset-only Zenodo
boundary.

After the redistribution gates in `THIRD_PARTY_NOTICES.md` are resolved,
populate the existing dataset-only draft from the validated shared release
manifest. Generated FDIA and additional paper datasets belong in named
collections within the same record family, with their own provenance and
generation manifests.
