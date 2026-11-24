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

LISTS_COLUMNS = [
    "list_id",         # e.g. EMODNET_BIOGENIC, GOOS_EOV, NRL_2024_MARINE
    "name",
    "kind",            # policy | observing variable | product | functional
    "version",
    "authority",
    "deliverable",     # WP3 deliverable(s) that use the list, e.g. D3.10
    "scope",
    "source",
    "accessed",        # date the source was obtained (ISO 8601); blank if not loaded
    "status",          # loaded | planned
    "notes",
]

LIST_ITEMS_COLUMNS = [
    "list_id",         # FK -> lists.list_id
    "item",            # item id within the list (e.g. mussel-beds, G1-MED, coral-cover-and-composition)
    "name",
    "level",           # hierarchical level within the list
    "parent_item",
    "definition",
    "attributes",      # e.g. regions; for EFH: species (AphiaID), life stage, function
    "source",
    "notes",
]

LIST_MEMBERS_COLUMNS = [
    "list_id",         # FK -> lists.list_id
    "item",            # FK -> list_items.item
    "region",          # region where the link applies (blank = all)
    "zone",            # biological zone where the link applies (blank = all)
    "system",          # classification of the member habitat (FK -> systems.system)
    "code",            # member habitat code (FK -> habitats.code)
    "link_type",       # member | partial | supports function | excluded
    "status",          # published | proposed | reviewed | rejected
    "source_relationship",  # relationship as given by the source (e.g. 'maps to', '>', '<')
    "decided_by",
    "decided_on",
    "source",
    "notes",
]

EXTRACTION_RULES_COLUMNS = [
    "list_id",            # FK -> lists.list_id, e.g. EMODNET_BIOGENIC
    "item",               # list item obtained by the rule
    "region",
    "data_source",        # data product queried (name, version, classification system)
    "spatial_scope",      # e.g. 'within the UK EEZ', blank = whole region
    "query",              # query string as published
    "result",             # whether polygons were returned (as published)
    "source",
    "notes",
]
