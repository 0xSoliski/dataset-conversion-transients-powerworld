# Third-Party Data and Model Notices

The MIT license in this repository applies only to original project code and
documentation. It does not relicense bundled third-party data or simulator
assets.

| Material | Upstream source | Current treatment | Publication gate |
| --- | --- | --- | --- |
| KIOS modified IEEE 118-bus dynamic case and derived PowerWorld exports | [KIOS Research Center, University of Cyprus](https://www.kios.ucy.ac.cy/testsystems/) | Attribution is recorded in the README and paper citation | The accessible article/record does not establish redistribution terms for the `.pwb` and `.pwd` files. Obtain the exact upstream license or written permission before public upload. |
| GEFCom2012 archive | [Global Energy Forecasting Competition 2012](https://blog.drhongtao.com/2016/07/gefcom2012-load-forecasting-data.html) | The author makes the data available for research use and requests citation, but no explicit redistribution license was found | Do not republish the raw archive or extracted upstream files until permission is documented. Provide the upstream link, citation, acquisition instructions, and checksums instead. |
| PSSE-via-DNNs MATLAB datasets | [Liang Zhang et al.](https://github.com/LiangZhangUMN/PSSE-via-DNNs) | Original files and source citation retained; the upstream repository has no explicit redistribution license | Do not republish the upstream `.mat` files until permission or a license is documented. Provide the source link, version/commit, acquisition instructions, and checksums instead. |
| PowerWorld Simulator case and output | [PowerWorld Corporation software](https://www.powerworld.com/files/Executable-PowerWorld-Simulator-Single-User-License-Agreement.pdf) | A modified case and exported research data are bundled | Confirm the institution's actual historical/academic license and obtain written permission covering publication and ML use. The current public single-user EULA is a warning signal but may not be the agreement that governed these experiments. |

No new public release should be created until every publication-gate item above
has a verifiable source URL or included license text. If redistribution cannot
be confirmed, exclude the affected payload from the public release and document
how an authorized user can acquire or regenerate it. Project-generated payloads
may be uploaded only when their own derivation and publication rights are
confirmed and they cannot reconstruct restricted upstream material.

The selected license for rights-cleared project dataset payloads is CC BY 4.0.
That choice does not change any publication gate in this file and does not
relicense excluded third-party material.

The machine-readable inventory at `datasets/release-manifest.json` marks these
payloads as `pending-review` or `pending-upstream-review`. Those statuses are
release gates, not statements that redistribution has already been authorized.

The existing Zenodo versions `10.5281/zenodo.20744598` and
`10.5281/zenodo.20744819` remain restricted while these gates are open. They are
preserved because their dataset payloads match the local repository, but their
code-containing archives are not public dataset release packages.

The dataset-only `v0.2.0` draft is record `21533592`, reserved DOI
`10.5281/zenodo.21533592`. It contains zero files and remains unpublished until
the gates below are resolved.

The GitHub default branch is already public and its historical commits contain
the same large payloads. Restricting Zenodo does not resolve that existing
distribution. Do not create further releases; replace the public repository
history with the separately authorized clean code-and-manifest history only
after the retained dataset subset and redistribution terms are settled.
