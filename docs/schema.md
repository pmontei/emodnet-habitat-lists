# Table schema

All tables are CSV, UTF-8, long format. Column lists are defined in
`src/emodnet_habitat_lists/schema.py`.

## systems
| Column | Meaning |
|---|---|
| system | Short id used in all tables (e.g. `EUNIS_M_2022`, `ANNEX_I`, `OSPAR_TD`). |
| name | Full name of the classification or list. |
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
| relationship | `=` same, `<` from is narrower, `>` from is broader, `#` overlap, or as given by the source: `partim` (marked "(partim)" in the source), `unspecified` (listed without qualifier), `source of` (the from habitat is the source the to habitat was derived from), `indicative` (published as indicative), `candidate` (derived, needs expert review), `maps to` (the from habitat is translated to the to type in a composite product), `maps to (with biological zone)`. |
| source | Provenance (file / sheet, or report + page). |
| notes | Free text. |

## composites
| Column | Meaning |
|---|---|
| composite | Product id (e.g. `EOV_SEAGRASS`, `VME`, `BIOGENIC_SUBSTRATE`). |
| deliverable | e.g. `D3.03`. |
| system, code | Habitat selected (or rejected). |
| include | `yes` / `no` / `review`. |
| rationale | Why. |
| decided_by, decided_on | Who and when. |
| source | Report + page, meeting, or decision note. |
