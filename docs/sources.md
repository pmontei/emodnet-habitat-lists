# Sources

Official source files are not stored in this repository. To rebuild the tables, place them in a
folder (default `data/raw/sources/`, or pass `--sources`) with the layout below; each sub-folder
also holds a `source.txt` with the full references, links and download dates.

PDF sources are read with `pdftotext` (poppler-utils), which must be installed.

## 1. EUNIS (EEA)

Folder: `1.EUNIS habitat classification/`

| System | Source | Link |
|---|---|---|
| `EUNIS_2012`, `EUNIS_M_2019`, `EUNIS_M_2022`, `EUNIS_T_2021` (habitats) | Currently read from `data/eunis_habitats.rda` of the R package `{eunis.habitats}` (Magno, Monteiro & Bentes), built from the official EEA files below; downloaded automatically. | https://github.com/ramiromagno/eunis.habitats |
| EUNIS marine 2022 (used for `BARCELONA_2006 -> EUNIS_M_2022`) | EEA, 2022. EUNIS marine habitat classification 2022 including crosswalks (published 28 Mar 2022). Path: `3_eea_t_eunis-hab-m_p_2004-2019_v01_r00/eea_t_eunis-hab-m_p_2004-2019_v01_r00/EUNIS marine habitat classification 2022 including crosswalks.xlsx` | https://www.eea.europa.eu/data-and-maps/data/eunis-habitat-classification-1/eunis-marine-habitat-classification-review-2022/eunis-marine-habitats-classification-2022 |
| All EUNIS versions | EEA Datahub, EUNIS habitat classification | https://www.eea.europa.eu/en/datahub/datahubitem-view/638330ea-90e6-4e41-81ea-e70f25ae7117 |

## 2. Barcelona Convention (UNEP/MAP – SPA/RAC)

Folder: `2.Barcelona Convention/` (files are matched by their numeric prefix).

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2019_*.pdf` | UNEP/MAP, 2019. Decision IG.24/7, COP21, Naples, Dec. 2019 (UNEP/MED IG.24/22). Annex VI: Updated Classification of Benthic Marine Habitat Types for the Mediterranean Region; Annex VII: Updated Reference List of Marine Habitat Types. | `BARCELONA_2019`, `BARCELONA_RL_2019` | https://www.rac-spa.org/sites/default/files/doc_cop/cop21/decision_24_7_eng.pdf |
| `02_2019_*.pdf` | SPA/RAC–UN Environment/MAP, 2019. Updated Classification of Benthic Marine Habitat Types for the Mediterranean Region. Tunis. | cross-check of `BARCELONA_2019` | https://www.rac-spa.org/sites/default/files/doc_fsd/habitats_list_en.pdf |
| `03_2021_*.pdf` | UNEP/MAP–SPA/RAC, 2021. Interpretation Manual of Marine Habitat Types in the Mediterranean Sea. UNEP/MED WG.502/Inf.4. | `BARCELONA_2019 -> EUNIS_M_2019 / EUNIS_2012 / ANNEX_I / CORINE` | https://www.rac-spa.org/meetings/nfp15/nfp_docs/inf/21wg502_inf04_en.pdf |
| `04_2021_*.pdf` | Montefalcone, M., Tunesi, L. & Ouerghi, A., 2021. Marine Environmental Research 169, 105387. | documentation of the coding system | https://doi.org/10.1016/j.marenvres.2021.105387 |
| `05_2006_*.pdf` | UNEP-MAP-RAC/SPA, 2006. Classification of Benthic Marine Habitat Types for the Mediterranean Region (adopted 1998/1999). | `BARCELONA_2006` | https://www.rac-spa.org/sites/default/files/doc_fsd/lchm_en.pdf |
| `06_2017_*.pdf` | UNEP-MAP-RAC/SPA. Handbook for interpreting types of marine habitat for the selection of sites to be included in the national inventories of natural sites of conservation interest (former codes). | not used yet | https://repository.oceanbestpractices.org/items/1ed0d4df-4303-48cb-a0b4-9ec68cced683 |
| `outras fontes/25_wg_606_5_en.pdf` | UNEP/MAP SPA/RAC, 2025. Assessment methodologies, assessment criteria and thresholds for biodiversity common indicators CI1 and CI2. UNEP/MED WG.606/5, Annex III: preliminary cross-walk Barcelona 2019 – EUNIS 2022 (Posidonia, coralligenous, maërl). | not used yet | https://spa-rac.org/uploads/CKFiles/files/25_wg_606_5_en.pdf |

### Coding of `BARCELONA_2019`

`M` + zone letter + substrate digit (EUNIS level 2, e.g. `MA1`) + `.5` (Mediterranean, level 3)
+ habitat digits (level 4, 5, ...). Facies beyond 9 use upper-case letters (`MC2.51A` = 10th
facies of `MC2.51`); a lower-case letter marks a variant of a habitat (`MB1.51a`) and is
inherited by its facies (`MB1.511a`, `MC1.51Ab`).

### Corrections of typos in the sources (`notes` column)

| System | Printed | Corrected | Where |
|---|---|---|---|
| `BARCELONA_2019` | `ME2.512 Facies with Brachiopoda` (under `MD3.51`) | `MD3.512` | Decision IG.24/7 and SPA/RAC 2019 |
| `BARCELONA_2006` | `V. 2. 2. 10. Facies with large Bryozoa` (under `IV.2.2`) | `IV.2.2.10` | 2006 classification |
| crosswalk | `11.4.1.4` | `II.4.1.4` | EEA EUNIS marine 2022, source code of `MA2552` |
| crosswalk | `III1.1` | `III.1.1` | EEA EUNIS marine 2022, source code of `MB152` |

### `BARCELONA_2006` ↔ `BARCELONA_2019`

**There is no official correspondence.** An SPA/RAC subregional report states that no handbook or
guide exists to compare the former list with the new classification. The `crosswalks` table holds:

* `indicative`: the few pairs published in that report (source in the `source` column);
* `candidate`: pairs derived through EUNIS (a 2006 code that is the EEA source of a EUNIS marine
  2022 habitat, and a 2019 code whose Interpretation Manual sheet cites the same EUNIS habitat).
  These are **candidates for expert review**, not correspondences.

The Interpretation Manual uses some codes that are not in the adopted classification
(e.g. `MC1.512`, `MC1.514c`); such rows are flagged in `notes` ("from_code not found in ...").
