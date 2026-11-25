# Attribute table templates of EMODnet Seabed Habitats data and composite products

Compiled from the EMODnet Data Exchange Format (DEF) and the WP3 product reports, to agree one
template per composite product. Files in `templates/`:

| File | Content |
|---|---|
| `templates.csv` | One row per template: product, deliverable, report and table, geometry, role (`input`, `product`, `reference`), notes. |
| `template_fields.csv` | One row per field: template, order, field name as printed, data type and length (when given), description, table of the report. |
| `field_matrix.csv` | Field (lower case) × template: which template uses which field, with the spelling of each report. |

Templates (15):

* **Inputs** — `DEF_MAP_2022` (habitat maps of the EMODnet catalogue, from the shapefile template
  `DEF_ShapefileTemplates_v2022` and the DEF document v4.1), `DEF_STUDYAREA_2022`, `POINTS_SAMPLE`
  (survey sample points, as given in the EOV points report).
* **Composite products** — biogenic substrate (`BIOGENIC_2021`, `BIOGENIC_PTS_CARIB_2023`), EOV
  (`EOV_PTS_2021`, `EOV_POLY_2025`, `EOV_PTS_2025`, `EOV_MANGROVE_2023`), coralligenous
  (`CORAL_PTS_2023`, `CORAL_POLY_2023`, `CORAL_PTS_2025`, `CORAL_POLY_2025`), VME (`VME_2025`).
* **Reference** — `EUSEAMAP_HAB` (EUSeaMap habitat layer, "Constructing EUSeaMap", Appendix 4).

## Families

1. **DEF polygon family** (catalogue maps): `GUI`, `POLYGON`, `ORIG_HAB`, `ORIG_CLASS`, `HAB_TYPE`,
   `HAB_CLASS`, translation fields (`DET_*`, `TRAN_COM`, `T_RELATE`), polygon groups (`COMP`,
   `COMP_TYPE`), confidence (`SUM_CONF`, `TEXT_CONF`).
2. **Point family** (survey sample points, Darwin Core-like): 23 fields from `measurementid` to
   `eventenddate`, plus product fields (`EOV`, `EOVsubtype` or `Coralligen`; `Source`).
3. **"EOV polygon" family** (EOV 2025, mangrove 2023, VME 2025): one column per classification
   (`Eunis_code/name`, `Anxi_code/name`, `Ai_subtype`, `Ospar_hab`, `habsubtype`, HELCOM in VME),
   `map_id`, `hab_origin`, `determiner`, `Det_date`, `source`.
4. **Minimal product templates**: biogenic (`BIO_DETAIL`, `SRC_NAME`), coralligenous polygons 2023
   (DEF translation fields + `orig_id` + `Coralligen`).

## Gaps and inconsistencies found

Errors in the reports

* **D3.14 coralligenous (2025), Appendix 2, Table 2** is titled "polygon data attribute table" but
  lists the first 11 *point* fields (`measurementid` … `seabedclassificationsystem`) and stops: the
  2025 polygon template is missing.
* The file `Reports/EOV/3.Gonçalves et al. - 2023 - … [D3.12].pdf` has exactly the same text as the
  2025 D3.11 EOV report (`4.20260205_…_D3.11_EOV_v1.pdf`); the 2023 D3.12 EOV report itself is not in
  the folder.
* D3.06 (2021) refers to "Table 5" and "'x' means that the type is thought to be present" inside
  the description of `BIO_DETAIL` (copied from the caption of another table); D3.12 (2025) repeats it
  and says "All source data products are listed in Table 2", which in that report is the attribute
  table itself.
* The 2025 mangrove report (D3.11) gives no attribute table.

Differences between templates of the same family

* **No common identifier of the source map**: `GUI` (DEF, Caribbean biogenic points), `Map_id` /
  `map_id` (EOV, mangrove, VME), `orig_id` (coralligenous polygons, D3.08 `ORIG_ID`), `SRC_NAME`
  (biogenic, product name, not map), `datasetid` (points).
* **No common original-habitat field**: `ORIG_HAB` + `ORIG_CLASS` (DEF), `Hab_origin` without the
  classification (EOV polygons, mangrove, VME), `orig_hab` without `orig_class` (coralligenous
  polygons 2023), `seabedtype` + `seabedclassificationsystem` (points).
* **Classification version not recorded**: `Eunis_code` holds "version 2007-2011 or 2022" in the
  same column (EOV 2025) with no version field; mangrove and VME do not say which version. Since
  several EUNIS 2022 codes were re-used with another meaning (see `EUNIS_M_2019 -> EUNIS_M_2022`),
  a code without its version is ambiguous.
* `Ai_subtype` is in EOV and mangrove but not in VME; `habsubtype` (OSPAR) is in mangrove and VME but
  not in EOV 2025.
* The product field differs: `EOV`/`EOVsubtype`, `Coralligen`, `BIO_DETAIL`, `VME_Habita`/
  `HabitatTyp`/`VME_Indica`. There is no common way to say which list / item of a composite
  product a feature belongs to, nor which version of that list was used.
* **No confidence field in any composite template**, although the overlap rules use the confidence
  score (biogenic, EOV). Only the DEF has `SUM_CONF` / `TEXT_CONF`.
* **No link type**: the composite templates do not record whether the source habitat belongs fully
  or partly to the product type (DEF `T_RELATE` exists only in the coralligenous 2023 polygons).
* Spelling of the same field changes between reports (`measurementid` / `measurementID`,
  `expectedcitation` / `ExpectedCitation`, `Source` / `source` / `SOURCE`, `Map_id` / `map_id`).
* Data types are given only in some reports; `Det_date` is Text (EOV 2025) or string (mangrove)
  while the DEF has a Date.
* **Shapefile field names over 10 characters** in VME 2025 (`Sum_fsh_int`, `Harm_fsh_int_m2`,
  `Harm_fsh_int_km2`, `Class_fsh_int`) are truncated in a shapefile; `Shape_leng`/`Shape_area` are
  geodatabase system fields.

## How the repository fills a composite template

For each feature extracted from a map in DEF format, the repository can supply:

| Template need | From the repository |
|---|---|
| product type (e.g. `EOV`, `Coralligen`, `BIO_DETAIL`) | `list_items` (`list_id`, `item`, `name`) |
| classification of the original habitat | `ORIG_CLASS` / `HAB_CLASS` → `systems.system` (alias table, to do) |
| relationship of the original habitat to the product type | `list_members.link_type` (`member` / `partial`) → `T_RELATE` (`<` / `#`) |
| justification | `list_members.source`, `status`, `decided_by`, `decided_on` |
| other classifications (EUNIS code/name, Annex I, OSPAR, HELCOM) | `crosswalks` from the original code, with version |
