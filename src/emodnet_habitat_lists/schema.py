"""Column definitions for the reference tables.

All tables are long-format so that every classification system can be stored side by side
and filtered with the same code. See ``docs/schema.md`` for a description of each column.
"""

SYSTEMS_COLUMNS = [
    "system",          # short id, e.g. EUNIS_M_2022, ANNEX_I, OSPAR_TD
    "name",            # full name of the classification / list
    "version",         # version or year
    "authority",       # issuing body (EEA, EC, OSPAR, UNEP/MAP-SPA/RAC, ...)
    "scope",           # geographic / thematic scope
    "source",          # file name or URL of the official source used
    "accessed",        # date the source was obtained (ISO 8601)
    "notes",
]

HABITATS_COLUMNS = [
    "system",          # FK -> systems.system
    "code",            # habitat code within the system
    "name",
    "level",           # hierarchical level (int, if the system is hierarchical)
    "parent_code",     # code of the parent habitat in the same system
    "realm",           # marine / terrestrial / ...
    "group",           # e.g. benthic / pelagic / ice-associated
    "description",
    "source",          # provenance of the row (file, sheet, or report + page)
    "notes",           # e.g. corrections of typos found in the source
]

CROSSWALKS_COLUMNS = [
    "from_system",
    "from_code",
    "to_system",
    "to_code",
    "relationship",    # =, <, >, # (overlap) or as given by the source
    "source",          # provenance of the crosswalk row
    "notes",
]

COMPOSITES_COLUMNS = [
    "composite",       # e.g. EOV_SEAGRASS, VME, BIOGENIC_SUBSTRATE
    "deliverable",     # e.g. D3.03
    "system",
    "code",
    "include",         # yes / no / review
    "rationale",
    "decided_by",
    "decided_on",
    "source",          # report + page, meeting, or decision note
]
