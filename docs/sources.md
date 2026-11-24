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

## 6. Habitats Directive Annex I (European Commission)

Folder: `6.EU Habitats Directive/` (files are matched by their numeric prefix).

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2013_*consolidated*.pdf` | Council Directive 92/43/EEC, consolidated version 01/07/2013 (CELEX 01992L0043-20130701), Annex I. | `ANNEX_I` (codes, names, groups, priority `*`) | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:01992L0043-20130701 |
| `02_1992_*original*.pdf` | Council Directive 92/43/EEC, original text (OJ L 206, 22.7.1992). | not used (historical) | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:31992L0043 |
| `03_2013_*Interpretation-Manual*EUR28*.pdf` | European Commission DG ENV, 2013. Interpretation Manual of European Union Habitats – EUR28 (April 2013). The original EC link no longer works; mirror used: Danish EPA. | `ANNEX_I` descriptions (section 1); `ANNEX_I -> PAL_CLASS`; `ANNEX_I -> EUNIS_2012` | https://sgavmst.dk/media/1ydgjxu4/int_manual_eu28.pdf (EEA record: https://eunis.eea.europa.eu/references/2435) |
| `04_2026_BISE_*.pdf` | BISE, Habitat types distribution and areas (EU27) dashboard (Article 17, 2013-2018). | not used (context) | https://biodiversity.europa.eu/ |
| EUNIS marine 2022 file (folder 1) | EEA 2022, columns "Annex I relationship" / "Annex I code". | `EUNIS_M_2022 -> ANNEX_I` | see section 1 |

Notes:

* Levels: 1 = habitat group (`1` … `9`), 2 = sub-group (`11`, `12` …), 3 = habitat type (233 types).
  Group 4 has no sub-groups, so its types have parent `4`. The `*` of priority types is removed from
  the name and recorded in `notes`.
* `realm` is assigned by this repository: `marine` for sub-group 11, 1610, 1620, 1650 and 8330;
  `coastal` for the rest of groups 1–2; `freshwater` for group 3; `terrestrial` for groups 4–9.
* Only three manual entries give EUNIS codes (1110, 1170, 1180), as "Relevant types within/under …"
  (EUNIS version 2.3, 2002): relationship `partim`. The EEA EUNIS marine 2022 crosswalk is the main
  link between EUNIS and Annex I; its relationship lists are paired with the Annex I codes by position.
* `PAL.CLASS.` items are split on commas and "and"; a trailing `p` (pro parte) gives `partim`.
  Compound expressions (`22.11 x 22.31`, `16.221 to 16.227`) are kept as printed. Some codes are
  marked "(1997 version)" in the manual (noted in `notes`).
* The Barcelona Interpretation Manual prints priority types as `1150*`; the `*` is removed in
  `BARCELONA_2019 -> ANNEX_I` and recorded in `notes`.

## 7. MSFD broad habitat types (European Commission)

Folder: `7.MSFD broad habitat types/`

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2017_*2017-848*.pdf` | Commission Decision (EU) 2017/848 of 17 May 2017 (OJ L 125, 18.5.2017, p. 43–74), Annex, Part II, theme "Benthic habitats", Table 2. | `MSFD_BHT`; `MSFD_BHT -> EUNIS_M_2022` | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017D0848 |

Notes:

* 22 benthic broad habitat types. **No official codes**: `code` is a slug of the name
  (e.g. `infralittoral-sand`).
* The Decision lists the "Relevant EUNIS habitat codes (version 2016)", level 2. Relationship `=`
  when one code is listed and `>` when several are (the broad habitat type contains each). These
  level-2 codes are unchanged in EUNIS marine 2022; every code `MA1` … `MG6` is used exactly once.

## 8. Marine Habitat Classification for Britain and Ireland (JNCC)

Folder: `8.Marine Habitat Classification for Britain and Ireland/`

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2022_JNCC_MHC-v22-04_*.xlsx` | JNCC, 2022. Marine Habitat Classification for Britain and Ireland v22.04, full biotope list. | `UK_MHC_2204` | https://mhc.jncc.gov.uk/resources/ |
| `02_2026_JNCC_*correlation*.xlsm` | JNCC, 2026. Marine habitat correlation tables v2026.02 ("Read Me" says 2026.01). | `UK_MHC_2204 ->` 16 systems (see below) | https://jncc.gov.uk/resources/ea153999-2892-4c62-919e-c33b33c65fda |
| `03_2026_*user-guide.pdf` | JNCC, 2026. Correlation tables user guide (March 2026). | relationship types | https://data.jncc.gov.uk/data/ea153999-2892-4c62-919e-c33b33c65fda/UserGuide-MarineHabitatsCorrelations.pdf |
| `04_2023_*`, `05_2019_*` | How to use MHC v22.04 (2023); Parry 2019, JNCC Report 546 (assigning biotopes using EUNIS or MHC). | documentation | https://mhc.jncc.gov.uk/resources/ |
| `06_2004_*` to `09_2004_*` | Connor et al., 2004. MHC v04.05 (introduction, biotope sections, comparative tables). | not used (v04.05 codes come from the correlation tables) | ISBN 1 861 07561 8 |

Notes:

* Correlation targets: `UK_MHC_1503`, `UK_MNCR_0405`, `UK_MHC_9706`, `EUNIS_M_2022`, `EUNIS_2012`
  (JNCC "EUNIS 2007"), `OSPAR_TD_2021`, `ANNEX_I`, `MSFD_BHT`, `ICES_VME`, `EMERALD`, `GOOS_EOV`,
  `IUCN_GET`, `UK_HPI`, `UK_MCZ_FOCI`, `UK_PMF`, `UK_MCZ_BSH`.
* Relationships: "Is the same as" `=`, "Contains" `>`, "Is contained within" `<`, "Partially overlaps with" `#`.
* OSPAR and VME are given by name; they are matched to the repository codes (aliases: "Kelp Forest",
  "Seapen and burrowing megafauna communities", "Modiolus modiolus horse mussel beds", "Seapen fields",
  "Lophelia pertusa /Madrepora oculata reef", "Solenosmilia variabilis reef"). The JNCC name is kept in `notes`.
  Other name-only lists (GOOS EOV, UK lists) are coded with a slug of the name.
* Inconsistencies between the two JNCC files (flagged as "from_code not found"):
  the correlation tables use `LR.FLR.CvOv.RpurPlac`, the biotope list `LR.FLR.CvOv.RpurPil`;
  `M.AtMB.Sa.InfPol` is in the correlation tables but not in the biotope list. In the biotope list,
  `M.AtLB.Sa.InfPol` is named "... in Atlantic mid bathyal sand".

## 9. Nature Restoration Regulation (EU) 2024/1991

Folder: `9.Restauration law/`

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2024_*2024-1991*.pdf` | Regulation (EU) 2024/1991 of 24 June 2024 on nature restoration (OJ L, 2024/1991, 29.7.2024), Annex II. | `NRL_2024`; `NRL_2024 -> EUNIS_M_2022`; `EUNIS_M_2022 -> ANNEX_I` | http://data.europa.eu/eli/reg/2024/1991/oj |

Notes:

* `NRL_2024` rows are the 7 groups (`G1` seagrass beds … `G7` soft sediments not deeper than 1 000 m)
  and their marine regions (`G1-ATL`, `G1-BAL`, `G1-BLS`, `G1-MED`). The 231 habitat types listed are
  EUNIS 2022 habitats, linked with `>` (the group/region contains the EUNIS type); the Annex II name
  is kept in `notes`.
* The "Related habitat type code" column (Annex I) comes from the EEA 2021 crosswalk according to the
  Regulation; relationship `unspecified`.

## 10. Black Sea

Folder: `10.Black Sea/`

* The Black Sea habitat units used are those of **EUNIS marine 2022**: level-3 codes ending in `4`
  (e.g. `MB54` Black Sea infralittoral sand) and their sub-units (52 level-3, 97 level-4 units,
  benthic and pelagic). Filter `habitats.csv` with `system == "EUNIS_M_2022"` and a code matching
  `^M[A-H][0-9A]4`.
* Grande et al., 2025. CoDeMap: a classification scheme for benthic habitats from the coast to the deep
  sea in the Mediterranean and Black Sea. Front. Mar. Sci. 12:1663369
  (https://doi.org/10.3389/fmars.2025.1663369), with its supplementary table (morphology, substrate,
  biology components): not used yet (a mapping scheme, not an adopted classification).

## 11. Biogenic substrate (EMODnet Seabed Habitats)

Folder: `11.Biogenic substrate/`

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2021_*Biogenic-substrate*.pdf` | Lillis, H., Allen, H., Agnesi, S., Annunziatellis, A. & Vasquez, M., 2021. A combined, harmonized data product showing the best evidence for the extent of biogenic substrate in Europe. EMODnet Seabed Habitats D3.05/D3.06. | `EMODNET_BIOGENIC_2021` (Table 5); Appendix 1 and 2 crosswalks | EMODnet Seabed Habitats reports (https://emodnet.ec.europa.eu/) |

Notes:

* Definition (section 1.1): beds or reefs of a species that, like *Posidonia oceanica* meadows, cover
  and replace the underlying substrate, can occur on different substrate types and are detectable
  acoustically. Stored as the `description` of `biogenic-substrate`.
* Typology (Table 5): 29 types in 4 levels, transcribed in `biogenic.TYPOLOGY` and checked against the
  PDF text by the tests; regions in `notes`. Codes are slugs of the names.
* Appendix 1 (EUNIS 2007-11, Annex I, HELCOM HUB, OSPAR → biogenic type): relationship `maps to`;
  region in `notes`. Annex I 1170 maps to biogenic substrate only for its biogenic subtype.
  Table 16 says "Sabellaria spinulosa beds" for the type "Sabellaria spinulosa reefs".
* Appendix 2 (biogenic type + biological zone + region → EUNIS 2019): relationship
  `maps to (with biological zone)`; zone, region, EUNIS 2007-11 code and the report's "unofficial
  corrections" in `notes`. The corrections add codes that are not in EUNIS 2019 (flagged "not found"):
  `MB2224`, `MC223`, `MC2237`, `MC2238`.
* Tables 6-9 (data source and query used to extract polygons for each type, by region) are in
  `extraction_rules.csv` (51 rules; result `y`/`n` as published, `miscoded`, `not applicable`).
  The UK list values used in the queries (Scottish PMFs, MCZ FOCI) also give `UK_PMF` /
  `UK_MCZ_FOCI -> EMODNET_BIOGENIC_2021` crosswalks. Queries are transcribed and checked word by
  word against the PDF by the tests. As printed: 'Modiolous modiolus' (OSPAR 2020 dataset value) and
  a missing '=' in one FOCI query (noted).
* **EUNIS 2022 vs the report's corrections:** EUNIS 2022 adopted `MC223` "Bivalve reefs in the
  Atlantic circalittoral zone" and the name fixes of `MB2211` and `MD22`, but codes the circalittoral
  *Mytilus edulis* and *Hiatella arctica* beds as `MC2235` and `MC2236` (the report proposed `MC2237`
  and `MC2238`), and has no `MB2224`. To be taken into account when updating the product to EUNIS 2022
  (D3.10).

## 12. Caribbean

Folder: `12.Caribbean/`

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2022_*Andres-et-al*.pdf` | Andres, S., Ferry, R., Gaudillat, V. & Dirberg, G., 2022. Typologie des habitats benthiques de la Martinique. PatriNat (OFB-CNRS-MNHN), 207 p. | `CARIB_MARTINIQUE_2022` (section 2, hierarchical tree); `-> FR_APHN_ANTILLES` (Annex 2) | https://mnhn.hal.science/mnhn-04136364v1 |
| `02_2023_*HabRef*.pdf` | Gaudillat, V. et al., 2023. HabRef v7.0, guide méthodologique. PatriNat. | documentation | https://mnhn.hal.science/mnhn-04077190 |

Notes:

* EUSeaMap Caribbean uses this typology ("the most comprehensive EUNIS-like classification of the
  Caribbean seabed habitats", EUSeaMap metadata). Names are kept in French.
* Levels: 1 zone (`A` supralittoral … `F` abyssal), 2 substrate (`C2`), 3 geomorphology (`C2-5`),
  4 assemblage (`C2-51`), 5 habitat (`C2-51.1`): 6 + 14 + 39 + 68 + 118 units. Bathyal and abyssal
  have only the substrate level.
* Inconsistencies in the publication: geomorphology `C2-11b` printed with a 'b' (C2-11 is also an
  assemblage code); `C4-42.3` listed under `C4-41` in the tree; Annex 2 prints `C4.33.1` for `C4-33.1`
  and `D1-31.1`/`D1-31.2` for the tree's `D1-11.1`/`D1-11.2` (matched by name); `C4-23.2` is missing
  from Annex 2; `C4-34.8` has no APHN equivalent (`X`).
* No crosswalk to EUNIS is published in the typology; the EUSeaMap Caribbean translation to EUNIS 2022
  level 2 / MSFD is to be documented from the EUSeaMap technical report. The HabRef table
  (https://inpn.mnhn.fr/habitat/cd_hab/34410) can replace the PDF parsing when available.

## 13. Bern Convention, Resolution No. 4 (Emerald Network)

Folder: `13.Bern Convention/`

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2019_*Resolution-4*.pdf` | Resolution No. 4 (1996), Revised Annex I using the EUNIS habitat classification (adopted 6 December 2019). | `EMERALD`; `EMERALD -> EUNIS_2012` | https://rm.coe.int/16807469e7 |
| `02_2019_*Interpretation-manual*.pdf` | Interpretation manual of the habitats listed in Resolution No. 4 (1996), 4th edition, T-PVS/PA (2019) 18. | `description`; `EMERALD -> ANNEX_I` | https://www.coe.int/en/web/bern-convention/documents1 |
| `03_2019_*Addition-marine-habitats*.pdf` | Evans, D., 2019. Addition of marine habitats to Resolution No. 4 (1996), T-PVS/PA (2019) 6. | background | https://rm.coe.int/addition-of-marine-habitats-to-resolution-no-4-1996-/168097199c |

Notes:

* 213 habitat types (17 marine, `A…`), coded with EUNIS 2012 codes and names, plus 9 group headings
  (level 1) and the `X` habitat complexes. The marine list is coarse: `A3`, `A4`, `A5` are whole
  EUNIS level-2 classes (A5 defined as the near-shore sublittoral down to 200 m), and `A6.1` and
  `A6.61` were added in 2019 so that all of Annex I 1170 Reefs is covered (deep-sea reefs of UK
  offshore SACs). The same codes are used by the JNCC correlation tables ("Emerald Habitat").
* `EMERALD -> ANNEX_I` follows the manual's wording, which the manual calls indicative: "Same as" `=`,
  "Included in"/"Part of" `<`, "Includes" `>`, "Can occur as part of the following" `occurs within`,
  otherwise `unspecified`. Only codes that exist in `ANNEX_I` are kept.
* `E1.13` and `X35` (Inland sand dunes) are not in EUNIS 2012 as loaded from eunis.habitats (flagged).
  `F2.2` has no description extracted from the manual.

## 14. European Red List of Habitats (2016)

Folder: `14.European Red List of Habitats/`

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2016_*Part1-Marine.pdf` | Gubbay, S., Sanders, N., Haynes, T. et al., 2016. European Red List of Habitats. Part 1. Marine habitats. European Commission. | `EU_REDLIST_2016` (Annex A) | https://doi.org/10.2779/032638 |
| `02_2016_*Part2-Terrestrial-freshwater.pdf` | Janssen, J.A.M., Rodwell, J.S. et al., 2016. European Red List of Habitats. Part 2. Terrestrial and freshwater habitats. | not used | https://doi.org/10.2779/091372 |
| EUNIS marine 2022 file (folder 1) | EEA 2022, columns "Red List relationship" / "Red List code (for EEA publication)". | `EUNIS_M_2022 -> EU_REDLIST_2016` | see section 1 |

Notes:

* 257 benthic habitat types (Baltic 61, North-East Atlantic 86, Mediterranean 47, Black Sea 63 incl.
  Sea of Marmara), with EU28 and EU28+ category and criteria in `notes`. Category totals checked
  against the report's Table 3.1.1 by the tests.
* **Codes:** the working codes printed in Annex A are not unique (`A5.62` twice in the NE Atlantic,
  `A5.53` twice, `A3.2x` twice in the Black Sea; one Marmara habitat has no code). The repository uses
  the EEA "code for EEA publication" (sea prefix + code, e.g. `NEAA5.67` for the *Modiolus* beds that
  Annex A prints as `A5.62`, `NEAA5.53A` for the Macaronesian seagrass beds, `BLSA1.4C` for the Marmara
  caves), assigned by sea, working code and name; the Annex A code is kept in `notes`.
* The EEA crosswalk also cites `RLA2.5a`–`RLA2.5d` (coastal salt marshes), which belong to Part 2
  (not loaded; flagged "not found").

## 15. Ramsar Convention, wetland types

Folder: `15.Ramsar/`

| File | Reference | Used for | Link |
|---|---|---|---|
| `01_2022_*Resolution-XI8*.pdf` | Ramsar COP11 Resolution XI.8 Annex 2 (Rev. COP14), Strategic Framework, Appendix B: Ramsar Classification System for Wetland Type. | `RAMSAR` | https://www.ramsar.org/sites/default/files/documents/library/cop11-res08-e-anx2_revcop14.pdf |
| `02_2024_*SC63-Doc19*.pdf` | Ramsar SC63 Doc. 19 Annex 1: Ramsar wetland classification system (STRP advice). | context | https://www.ramsar.org/sites/default/files/2024-11/SC63%20Doc.19%20Annex%201%20Ramsar%20wetland%20classification%20system.pdf |
| `03_2024_*Crosswalk-Ramsar-IUCN-GET*.pdf` | DHI et al., 2024. Classification cross-walk V0.2, Ramsar → IUCN GET and SDG 6.6.1 (EO4WI, ESA). | `RAMSAR -> IUCN_GET` | — |

Notes:

* 43 wetland types since COP14: 13 marine/coastal (A–K, **Ga Bivalve (shellfish) reefs**, Zk(a)),
  20 inland, 10 human-made (1–9, Zk(c)); level-1 group codes `MC`, `IN`, `HM` are assigned by this
  repository. `name` = text before the first ';' of the Appendix B entry, `description` = full entry.
  Appendix E of the same document gives guidance on specific types (mangroves, coral reefs, bivalve
  reefs ...). The SC63 document still counts 42 types (12 marine/coastal).
* `RAMSAR -> IUCN_GET` (75 rows, relationship `indicative`): each EFG printed against a Ramsar type in
  the EO4WI draft. A (shallow marine waters < 6 m), B (subtidal aquatic beds), C (coral reefs),
  Ga (bivalve reefs, not in its source list), Zk(a) and Zk(c) have no EFG there.
