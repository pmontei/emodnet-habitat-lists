# Table schema

All tables are CSV, UTF-8, long format. Column lists are defined in
`src/emodnet_habitat_lists/schema.py`.

## systems
| Column | Meaning |
|---|---|
| system | Short id used in all tables (e.g. `EUNIS_M_2022`, `ANNEX_I`, `OSPAR_TD`). |
| name | Full name of the classification. |
| version | Version or year. |
| authority | Issuing body (EEA, EC, OSPAR, UNEP/MAP SPA/RAC, HELCOM, FAO/ICES…). |
| scope | Geographic / thematic scope. |
| source | File name or URL of the official source used. |
| accessed | Date the source was obtained (ISO 8601). |
| notes | Free text. |

## habitats
| Column | Meaning |
|---|---|
| system | FK to `systems.system`. |
| code | Habitat code within the system. |
| name | Habitat name. |
| level | Hierarchical level (1 = top). |
| parent_code | Code of the parent at `level - 1` in the same system (derived from the code). |
| realm | marine / terrestrial / … |
| group | e.g. benthic / pelagic / ice-associated. |
| description | Official description, when available. |
| source | Provenance of the row. |
| notes | Free text, e.g. corrections of typos found in the source. |

## crosswalks
| Column | Meaning |
|---|---|
| from_system, from_code | Origin habitat. |
| to_system, to_code | Target habitat. |
| relationship | `=` same, `<` from is narrower, `>` from is broader, `#` overlap, or as given by the source: `partim` (marked "(partim)" in the source), `unspecified` (listed without qualifier), `source of` (the from habitat is the source the to habitat was derived from), `indicative` (published as indicative), `candidate` (derived, needs expert review), `maps to` / `maps to (with biological zone)` (used by source modules for list links; these rows are moved to `list_members`). |
| source | Provenance (file / sheet, or report + page). |
| notes | Free text. |

## Classifications and lists

`systems`, `habitats` and `crosswalks` hold **classifications**: typologies in which maps and points
are classified directly. `lists`, `list_items` and `list_members` hold **lists**: selections,
groupings or functions defined on top of classifications (GOOS EOVs, Nature Restoration Regulation
groups, biogenic substrate, coralligenous, Essential Fish Habitat). A list item can have members in
several classifications at once (e.g. biogenic `mussel-beds` in EUNIS 2007-11, EUNIS 2019, EUNIS
2022 and HELCOM HUB), so a list survives a new version of a classification: only its members change.

## lists
| Column | Meaning |
|---|---|
| list_id | Short id (e.g. `EMODNET_BIOGENIC`, `GOOS_EOV`, `NRL_2024_MARINE`, `EFH`). |
| name | Full name. |
| kind | `policy` (legal or conservation list), `observing variable` (EOV), `product` (EMODnet composite product), `functional` (EFH), `dataset vocabulary` (values used in a dataset, e.g. the EMODnet OSPAR habitats dataset). |
| version | Version or year. |
| authority | Issuing body. |
| deliverable | WP3 deliverable(s) that use the list. |
| scope | Geographic / thematic scope. |
| source | Official source used. |
| accessed | Date the source was obtained (blank if not loaded). |
| status | `loaded`, `planned`, or `not loaded in this build`. |
| notes | Free text. |

## list_items
| Column | Meaning |
|---|---|
| list_id | FK to `lists.list_id`. |
| item | Item id within the list (e.g. `mussel-beds`, `G1-MED`, `coral-cover-and-composition`). For EFH: species × life stage × function. |
| name | Item name. |
| level, parent_item | Hierarchy within the list. |
| definition | Definition as published. |
| attributes | e.g. regions where the item applies; for EFH: species (AphiaID), life stage, function. |
| source | Provenance. |
| notes | Free text. |

## list_members
| Column | Meaning |
|---|---|
| list_id, item | FK to `list_items`. |
| region | Region where the link applies (blank = all). |
| zone | Biological zone where the link applies (blank = all), e.g. Appendix 2 of the biogenic report. |
| system, code | Member habitat (FK to `habitats`). When the member is an item of another list (e.g. a UK PMF item linked to a biogenic type), `system` is that `list_id` and `code` its item. |
| link_type | How the habitat belongs to the item: `member` (the whole habitat), `partial` (only part of it, e.g. Annex I 1170 only for its biogenic subtype; also when the habitat is broader than or overlaps the item), `supports function` (the habitat supports the function of the item, e.g. a nursery for an EFH item; not an equivalence), `excluded` (examined and left out on purpose). |
| status | Stage of the decision: `published` (as in the source), `proposed` (derived in this repository), `reviewed` (accepted by WP3), `rejected`. |
| source_relationship | Relationship as given by the source (`maps to`, `>`, `<`, `candidate`…). |
| decided_by, decided_on | Who and when (for `proposed`, `reviewed`, `rejected`). |
| source | Provenance. |
| notes | Free text; proposed members that need attention start their reason with `TO REVIEW:`. |

## extraction_rules

Rules used to build composite products from habitat maps: which data source and query give each
list item, by region, as published in the product reports.

| Column | Meaning |
|---|---|
| list_id, item | List item obtained (FK to `list_items`). |
| region | Region where the rule applies. |
| data_source | Data product queried (name, version, classification system). |
| spatial_scope | Restriction within the region (e.g. "within the UK EEZ"); blank = whole region. |
| query | Query string as published. |
| result | Whether polygons were returned (as published). |
| source | Report and table. |
| notes | |
