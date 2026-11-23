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

## 3. HELCOM HUB

Folder: `3.HELCOM HUB/`

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2013_HELCOM_BSEP139_HUB-Technical-Report.pdf` | HELCOM, 2013. HELCOM HUB – Technical Report on the HELCOM Underwater Biotope and habitat classification. Baltic Sea Environment Proceedings No. 139. | `HELCOM_HUB`: the 328 units of Annex 1 and the 10 biotope complexes | https://helcom.fi/wp-content/uploads/2019/08/BSEP139.pdf |
| `02_2013_HELCOM_BSEP138_Red-List-Biotopes.pdf` | HELCOM, 2013. Red List of Baltic Sea underwater biotopes, habitats and biotope complexes. Baltic Sea Environment Proceedings No. 138. | Red List category (`notes`): Annex 2 (biotopes) and Table 13 (complexes) | https://helcom.fi/wp-content/uploads/2019/10/BSEP138.pdf |
| `fact sheets/*.pdf` (387) | HELCOM HUB biotope fact sheets (HELCOM Red List Biotope Expert Team); file name = HUB code. | names of the higher levels; `HELCOM_HUB -> EUNIS_2012 / HELCOM_1998` | https://maps.helcom.fi/website/hub/PDF/ |
| EUNIS marine 2022 (EEA, folder 1) | 'Source classification system code' where the source is HELCOM HUB (2013). | `HELCOM_HUB -> EUNIS_M_2022` | see section 1 |

Notes:

* Annex 1 of BSEP 139 lists 328 units: 207 photic and 115 aphotic benthic biotopes, 1 sea-ice
  habitat and 5 pelagic habitats. The 68 higher levels (`A`, `AA`, `AA.A`, `AA.A1` ...) come from
  the fact sheets (group `higher level`). Biotope complexes use Habitats Directive Annex I codes
  (group `biotope complex`, no level).
* **Code inconsistencies between HELCOM documents:** BSEP 138 (Red List) and the fact sheets use
  `AA.H3M6` / `AB.H3M6` and `AA.J3M5` / `AB.J3M5` for the biotopes coded `AA.H3M5` / `AB.H3M5` and
  `AA.J3M4` / `AB.J3M4` in BSEP 139 Annex 1 (matched by name; recorded in `notes`). The fact sheet
  file `AB.J2K7.pdf` is biotope `AB.J3L7`.
* 11 Annex 1 biotopes have no fact sheet (AA.H1B3, AA.H1K, AA.H1S, AA.H1S3, AA.H3L1, AA.J1Q2,
  AA.M1G1, AB.E1F, AB.H3M, AB.H3M5, AB.M1F).
* Some fact-sheet correspondences look wrong (e.g. `AA.A1C1`, photic rock with *Fucus*, points to
  HELCOM 1998 2.8.1 and EUNIS A5.412, aphotic mixed sediment). They are loaded as published; only the
  most specific code of each listed path is kept.
* The EEA EUNIS marine 2022 file cites 17 HUB codes that do not exist in HELCOM HUB (e.g. `AA.C1E`,
  `AA.D1E`, `AB.C1E`, `AA.J3M34`); these rows are flagged in `notes`. Codes are printed with spaces
  and '(modified)' in that file (e.g. `AA.A 1C1(modified)`), normalised here; relationship
  `source of (modified)`.

## 4. OSPAR List of Threatened and/or Declining Habitats

Folder: `4.OSPAR/` (one sub-folder per habitat, named after the OSPAR website slug).

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2021_OSPAR_Agreement-2008-06_List.pdf` | OSPAR Commission, 2008 (amended 2021). OSPAR List of Threatened and/or Declining Species and Habitats. Agreement 2008-06, Part II - Habitats. | `OSPAR_TD_2021` names and OSPAR Regions (**transcribed in `sources/ospar.py`: the PDF has no text layer**) | https://www.ospar.org/documents?v=32794 |
| Agreement 2008-07 (not in folder) | OSPAR Commission, 2008 (revised 2021 to include Haploops habitat and Kelp forest). Descriptions of habitats on the OSPAR List. | sub-types; Haploops EUNIS / HELCOM relationship (transcribed) | mirror: https://inpn.mnhn.fr/docs-web/docs/download/394918 |
| `<habitat>/*_definition.pdf` (16) | Per-habitat extracts of Agreement 2008-07 published by OSPAR. | `OSPAR_TD_2021 -> EUNIS_2012 / UK_MNCR_0405` | https://www.ospar.org/site/assets/files/44271/ |
| `kelp-forest/p00787_kelp_case_report.pdf` | OSPAR, 2021. Case report for kelp forest habitat (publication 787), Appendix I. | `OSPAR_TD_2021 -> EUNIS_2012` (kelp forest, indicative) | https://www.ospar.org/documents?v=46871 |
| `EMODnet_OSPAR2025_habtype_habsubtype_values.csv` | Distinct `habtype` / `habsubtype` values of the EMODnet Seabed Habitats WFS layers `emodnet_view:ospar2025_points` and `ospar2025_polygons` (queried 2026-11-23; complete counts). | `OSPAR_TD_2021 -> EMODNET_OSPAR2025` | https://ows.emodnet-seabedhabitats.eu/geoserver/emodnet_view/wfs |

Notes:

* **OSPAR habitats have no official codes.** Codes are the OSPAR website slugs (e.g. `zostera-beds`);
  sub-types are `<habitat>/<sub-type>`; the sub-type numbers of Agreement 2008-07 (8.1, 8.2, 9.1, 9.2)
  are kept in `notes`.
* `name` is the official name in Agreement 2008-06. Names differ in a few places: Agreement 2008-07 and
  the EMODnet dataset use "Modiolus modiolus horse mussel beds"; EMODnet uses "Haploops" for "Haploops
  habitat". The link to the EMODnet values is in `crosswalks` (`to_system = EMODNET_OSPAR2025`).
* EMODnet kelp sub-types ("Kelp forests dominated by ...") are not OSPAR sub-types: relationship `>`.
* Data-quality issues in the EMODnet dataset: "Zostera noltii" / "Zostera noltei"; "Not Applicable" /
  "Not applicable"; no *Cymodocea meadows* records.
* The EUNIS codes of Agreement 2008-07 refer to EUNIS 2004; all are present in `EUNIS_2012`.
* Erratum: Agreement 2008-07 prints the HELCOM HUB code of the Haploops biotope as `AB.H1l2`; the HUB code is `AB.H1I2`.

## 5. Vulnerable Marine Ecosystems (ICES / FAO)

Folder: `5.VME (FAO  ICES)/`

| File | Reference | Used for | Link |
|---|---|---|---|
| `04_2023_ICES_vocab_VME-HabitatType-Subtype.csv` | ICES Vocabulary Server, code types HabitatType (ref 1410) and HabitatSubtype (ref 1411), last modified 2023-09-21; transcribed 2026-11-23. | `ICES_VME` | https://vocab.ices.dk/?ref=1410 ; https://vocab.ices.dk/?ref=1411 |
| `01_2020_ICES_VME-habitat-types-and-taxa.pdf` | ICES, 2020. A suggestive list of deep-water VMEs and their characteristic taxa. | not used yet (indicator taxa) | https://www.ices.dk/data/Documents/VME/VMEs%20and%20their%20taxa.pdf |
| `02_2009_FAO_International-Guidelines-Deep-sea-Fisheries-High-Seas.pdf` | FAO, 2009. International Guidelines for the Management of Deep-sea Fisheries in the High Seas. | VME criteria (documentation) | https://openknowledge.fao.org/server/api/core/bitstreams/224f4e53-0c34-4680-ad61-18e497763954/content |

Notes: deprecated ICES codes are kept and flagged in `notes`. ICES does not publish the habitat type
of each subtype; `parent_code` of subtypes is inferred from codes and names.
