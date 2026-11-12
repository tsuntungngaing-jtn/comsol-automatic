# Evidence provenance

Status: **implemented** ledger + schema; offline figure extraction is **IMPLEMENTED in v0.6.0** via `paper_figure_analyze` (manual ROI/calibration and optional OCR); full autonomous text/PDF claim extraction remains **NOT_IMPLEMENTED**.

| Mechanism | Basis | Support class |
|---|---|---|
| Separate value, origin, certainty, source, admissibility | Liu et al., Notes2Skills, arXiv:2606.11897 | LITERATURE_SUPPORTED |
| No promotion after a successful match | Liu et al. | LITERATURE_SUPPORTED |
| Source identity and conflict retention | Miao et al. Nature 2026 | LITERATURE_ADAPTED |
| Origin enumeration and source ranks | this repository | DESIGN_POLICY |

## Origin taxonomy

`reported` | `derived` | `library` | `documented_default` | `assumption` | `user_supplied` | `fitted` | `missing` | `inferred` | `digitized_estimate`

Origin is not certainty. Example: `origin=reported` and `certainty=ambiguous`. Example: `origin=library` and `certainty=exact_for_installed_library` still does not claim the paper used that library value.

## No-promotion rule

Never relabel `library`, `fitted`, `assumption`, `user_supplied`, `documented_default`, or `derived` as `reported`. User approval of a library candidate: `origin=library`, `decision=user_approved`.

## Conflicts

If candidates disagree, status=`conflict`; keep all candidates. Do not auto-pick. Weaker sources must not overwrite stronger ones; rank (DESIGN_POLICY): paper > supplement > author code/data > figure/table > reference implementation > installed docs > application library > material library.

Digitized figure samples use origin `digitized_estimate` (not `reported`); the ledger and evidence-record JSON Schema both recognize it as of v0.7.0. Offline intake remains a separate candidate review layer, not proof of scientific validity. See [offline input intake](offline-input-intake.md). Peer CFD priors use `INFERRED`+`LITERATURE` with DOI/table. Official feature-class defaults use `DEFAULT` / `[SOFTWARE_DOC_DEFAULT: locus]`. See [rsi-autonomy-profiles](rsi-autonomy-profiles.md).

## Intake order (identity preserved)

1. Main paper 2. SI 3. Author code 4. Author data 5. Figure/table 6. Reference implementation 7. Installed-version documentation 8. Official Application Library 9. Installed Material Library
