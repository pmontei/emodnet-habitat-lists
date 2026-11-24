"""Thematic lists that cut across classification systems (``lists``, ``list_items``, ``list_members``).

A **classification** (EUNIS, HELCOM HUB, Barcelona, JNCC MHC, Annex I, OSPAR, Ramsar, IUCN GET...)
is a typology in which map polygons or points are classified directly. It is stored in
``systems`` / ``habitats`` and linked to other classifications in ``crosswalks``.

A **list** is a selection, grouping or function defined on top of one or more classifications:
GOOS Essential Ocean Variables, the marine groups of the Nature Restoration Regulation, the EMODnet
biogenic substrate types, coralligenous, Essential Fish Habitat... Nobody classifies a map "in"
a list; habitats are selected for it. A list has

* ``list_items``: its categories, with their definitions (e.g. EOV ``seagrass-cover-and-composition``,
  NRL group ``G1-MED``, biogenic type ``mussel-beds``; for EFH: species x life stage x function);
* ``list_members``: the habitats of any classification linked to each item, with ``link_type``
  (``member``, ``partial``, ``supports function``, ``excluded``) and ``status`` (``published`` as
  in the source, ``proposed`` by us, ``reviewed``, ``rejected``).

The source modules still parse the lists as if they were systems (``habitats`` / ``crosswalks``
rows); :func:`split` moves those rows into the three list tables.
"""

from __future__ import annotations

import re

import pandas as pd

from .schema import LIST_ITEMS_COLUMNS, LIST_MEMBERS_COLUMNS, LISTS_COLUMNS

# system id used by the source module -> list metadata
LISTS = {
    "EMODNET_BIOGENIC_2021": dict(
        list_id="EMODNET_BIOGENIC", kind="product", deliverable="D3.10",
        name="EMODnet Seabed Habitats biogenic substrate types",
        version="2021 typology (D3.06); EUNIS 2022 members proposed for D3.10",
        authority="EMODnet Seabed Habitats", scope="European seas"),
    "GOOS_EOV": dict(
        list_id="GOOS_EOV", kind="observing variable", deliverable="",
        name="GOOS Biology and Ecosystems Essential Ocean Variables (habitat EOVs)",
        version="August 2026", authority="Global Ocean Observing System (GOOS)", scope="global"),
    "NRL_2024": dict(
        list_id="NRL_2024_MARINE", kind="policy", deliverable="",
        name="Nature Restoration Regulation (EU) 2024/1991: groups of marine habitat types (Annex II)",
        version="2024", authority="European Parliament and Council", scope="EU marine waters"),
}

_UK = dict(kind="policy", deliverable="", version="as in JNCC correlation tables v2026.02")
LISTS |= {
    "UK_PMF": dict(list_id="UK_PMF", name="Priority Marine Features (Scotland): habitats",
                   authority="NatureScot / JNCC", scope="Scotland", **_UK),
    "UK_MCZ_FOCI": dict(list_id="UK_MCZ_FOCI", name="Marine Conservation Zone habitat Features of Conservation Importance",
                        authority="Defra / JNCC", scope="England, Wales, UK offshore", **_UK),
    "UK_HPI": dict(list_id="UK_HPI", name="Habitats of Principal Importance (UK)",
                   authority="UK nature conservation bodies", scope="UK", **_UK),
    "UK_MCZ_BSH": dict(list_id="UK_MCZ_BSH", name="Marine Conservation Zone Broad-Scale Habitats",
                       authority="Defra / JNCC", scope="England, Wales, UK offshore", **_UK),
    "BARCELONA_RL_2019": dict(
        list_id="BARCELONA_RL_2019", kind="policy", deliverable="", version="2019",
        name="Barcelona Convention: Reference List of marine habitat types for the selection of sites "
             "(Decision IG.24/7, Annex VII)", authority="UNEP/MAP - SPA/RAC", scope="Mediterranean, benthic"),
    "EMODNET_OSPAR2025": dict(
        list_id="EMODNET_OSPAR2025", kind="dataset vocabulary", deliverable="", version="2025",
        name="EMODnet Seabed Habitats OSPAR habitats dataset: habtype / habsubtype values",
        authority="EMODnet Seabed Habitats", scope="North-East Atlantic"),
}
# lists whose items share the codes of a classification: item -> same code in that classification
SAME_CODE_MEMBERS = {"BARCELONA_RL_2019": "BARCELONA_2019"}
_ITEM_NAME = re.compile(r"(?:^|; )JNCC name: ([^;]+)")

PLANNED = [
    dict(list_id="CORALLIGENOUS", kind="product", deliverable="D3.09a",
         name="Coralligenous and other calcareous bio-concretions", version="", authority="EMODnet Seabed Habitats",
         scope="Mediterranean", source="", status="planned",
         notes="update of the coralligenous composite product (SPA/RAC request)"),
    dict(list_id="EFH", kind="functional", deliverable="D3.07",
         name="Essential Fish Habitat", version="", authority="EMODnet Seabed Habitats", scope="European seas",
         source="", status="planned",
         notes="items = species (AphiaID) x life stage x function (spawning, nursery, feeding, migration); "
               "links to habitat types, when any, are 'supports function', never equivalences"),
]

PROPOSED_RELATIONSHIPS = {"candidate"}
_REGION = re.compile(r"(?:^|; )region: ([^;]+)")
_ZONE = re.compile(r"(?:^|; )biological zone: ([^;]+)")
_NRL_REGION = {"ATL": "Atlantic", "BAL": "Baltic Sea", "BLS": "Black Sea", "MED": "Mediterranean"}


def _region_zone(list_system: str, item: str, notes: str) -> tuple[str, str]:
    notes = notes if isinstance(notes, str) else ""
    if list_system == "NRL_2024":
        return _NRL_REGION.get(item.rsplit("-", 1)[-1], ""), ""
    r, z = _REGION.search(notes), _ZONE.search(notes)
    region = r.group(1).strip() if r else ""
    return ("" if region == "all" else region), (z.group(1).strip() if z else "")


def _link_type(notes: str, relationship: str, habitat_is_from: bool) -> str:
    """``partial`` when only part of the habitat belongs to the item: the habitat is broader than or
    overlaps the item (``>`` / ``#`` read from the habitat), a proposed ``#``, or the source says so
    (e.g. Annex I 1170 -> biogenic substrate: "Reefs - biogenic subtype only")."""
    notes = notes if isinstance(notes, str) else ""
    if habitat_is_from and relationship in {">", "#", "partim"}:
        return "partial"
    if re.search(r"\bsubtype only\b|\bpartim\b|proposed relationship '[#>]'", notes):
        return "partial"
    return "member"


def split(habitats: pd.DataFrame, crosswalks: pd.DataFrame, systems_meta: dict[str, str], today: str,
          review: dict[tuple[str, str], str] | None = None):
    """Move list rows out of ``habitats`` / ``crosswalks``.

    ``systems_meta``: list system id -> source label. ``review``: (system, code) -> reason, for
    proposed members that need review (from :mod:`composites`).
    Returns (habitats, crosswalks, lists, list_items, list_members)."""
    review = review or {}
    in_list = habitats.system.isin(LISTS)
    items = habitats[in_list]
    lists_rows = []
    for sys_id, meta in LISTS.items():
        loaded = (items.system == sys_id).any()
        lists_rows.append({**meta, "source": systems_meta.get(sys_id, ""), "accessed": today if loaded else "",
                           "status": "loaded" if loaded else "not loaded in this build", "notes": ""})
    lists_rows += [{**p, "accessed": ""} for p in PLANNED]
    lists_df = pd.DataFrame(lists_rows, columns=LISTS_COLUMNS)

    items_df = pd.DataFrame({
        "list_id": items.system.map(lambda s: LISTS[s]["list_id"]), "item": items.code, "name": items.name,
        "level": items.level, "parent_item": items.parent_code, "definition": items.description,
        "attributes": items.notes.fillna("").str.extract(r"(regions: [^;]+)", expand=False).fillna(""),
        "source": items.source,
        "notes": items.notes.fillna("").str.replace(r"(; )?regions: [^;]+", "", regex=True).str.strip("; ")},
        columns=LIST_ITEMS_COLUMNS)
    # lists given only by name in the crosswalks (UK lists, EMODnet dataset values): items from there
    extra = []
    for sys_id, meta in LISTS.items():
        if (items.system == sys_id).any():
            continue
        side = pd.concat([
            crosswalks.loc[crosswalks.to_system == sys_id, ["to_code", "notes", "source"]]
            .rename(columns={"to_code": "code"}),
            crosswalks.loc[crosswalks.from_system == sys_id, ["from_code", "notes", "source"]]
            .rename(columns={"from_code": "code"})])
        for code, g in side.groupby("code", sort=True):
            m = _ITEM_NAME.search(str(g.notes.iloc[0]))
            name = m.group(1).strip() if m else re.sub(r"^habtype=", "", code).replace(" | habsubtype=", " / ")
            extra.append({"list_id": meta["list_id"], "item": code, "name": name, "level": None,
                          "parent_item": None, "definition": None, "attributes": "",
                          "source": g.source.iloc[0], "notes": "item named in the source of the links only"})
    if extra:
        items_df = pd.concat([items_df, pd.DataFrame(extra, columns=LIST_ITEMS_COLUMNS)], ignore_index=True)
        for x in extra:
            lists_rows_status = lists_df.list_id == x["list_id"]
            lists_df.loc[lists_rows_status, ["status", "accessed"]] = ["loaded", today]

    is_from, is_to = crosswalks.from_system.isin(LISTS), crosswalks.to_system.isin(LISTS)
    rows = []
    for _, r in crosswalks[is_from | is_to].iterrows():
        if r.from_system in LISTS and r.to_system in LISTS:
            # link between two lists (e.g. UK PMF -> biogenic type): the member is an item of the other list
            lsys, item, msys, mcode = r.to_system, r.to_code, LISTS[r.from_system]["list_id"], r.from_code
        elif r.from_system in LISTS:
            lsys, item, msys, mcode = r.from_system, r.from_code, r.to_system, r.to_code
        else:
            lsys, item, msys, mcode = r.to_system, r.to_code, r.from_system, r.from_code
        region, zone = _region_zone(lsys, item, r.notes)
        proposed = r.relationship in PROPOSED_RELATIONSHIPS or "proposed" in str(r.source).lower() \
            or (lsys == "EMODNET_BIOGENIC_2021" and msys == "EUNIS_M_2022")
        notes = r.notes if isinstance(r.notes, str) else ""
        if (msys, mcode) in review and lsys == "EMODNET_BIOGENIC_2021" and msys == "EUNIS_M_2022":
            notes = f"{notes}; TO REVIEW: {review[(msys, mcode)]}".lstrip("; ")
        rows.append({
            "list_id": LISTS[lsys]["list_id"], "item": item, "region": region, "zone": zone,
            "system": msys, "code": mcode, "link_type": _link_type(notes, r.relationship, r.from_system not in LISTS), "status": "proposed" if proposed else "published",
            "source_relationship": r.relationship,
            "decided_by": ("proposal (repository), pending WP3 review" if proposed else ""),
            "decided_on": today if proposed else "", "source": r.source, "notes": notes})
    for lsys, csys in SAME_CODE_MEMBERS.items():
        known = set(habitats.loc[habitats.system == csys, "code"])
        for _, it in items[items.system == lsys].iterrows():
            if it.code in known:
                rows.append({"list_id": LISTS[lsys]["list_id"], "item": it.code, "region": "", "zone": "",
                             "system": csys, "code": it.code, "link_type": "member", "status": "published",
                             "source_relationship": "same code", "decided_by": "", "decided_on": "",
                             "source": it.source, "notes": "the list uses the codes of the classification"})
    members_df = pd.DataFrame(rows, columns=LIST_MEMBERS_COLUMNS)
    return habitats[~in_list], crosswalks[~(is_from | is_to)], lists_df, items_df, members_df


def validate_members(members: pd.DataFrame, items: pd.DataFrame, habitats: pd.DataFrame) -> pd.DataFrame:
    """Flag members whose item or habitat code does not exist."""
    known = {s: set(g["code"]) for s, g in habitats.groupby("system")}
    known_items = set(zip(items.list_id, items["item"]))
    m = members.copy()
    for i, r in m.iterrows():
        flags = []
        if (r["list_id"], r["item"]) not in known_items:
            flags.append(f"item not found in {r.list_id}")
        if r.system in known and r.code not in known[r.system] and f"not found in {r.system}" not in str(r.notes):
            flags.append(f"code not found in {r.system}")
        elif r.system not in known and (r.system, r.code) not in known_items:
            flags.append(f"member not found in {r.system}")
        if flags:
            m.at[i, "notes"] = "; ".join([x for x in [r.notes if isinstance(r.notes, str) else ""] + flags if x])
    return m
