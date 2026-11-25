"""Product list ``EOV_SEAGRASS``: the habitats used to build the Seagrass cover EOV composite (D3.03).

The list says which habitat of which classification goes into the seagrass composite, so that
polygons and points of the EMODnet map library can be filtered by ``ORIG_HAB`` / ``ORIG_CLASS``
or ``HAB_TYPE`` / ``HAB_CLASS``. It implements the sub-variable "Areal Extent" of the GOOS EOV
``seagrass-cover-and-composition`` (list ``GOOS_EOV``).

Members come in three layers
----------------------------
1. **Published** (``status = published``), transcribed from the earlier EMODnet reports; every code
   is checked against the PDF text by the tests:

   * O'Keeffe & Lillis (2019), *Generating Essential Ocean Variables*: Table 2 (EUNIS 2007-11),
     Table 5 (OSPAR) and Table 6 (Annex I);
   * Gonçalves et al. (2025), D3.11 EOV report, Appendix Table 3 (EUNIS 2019, EUNIS 2007-11,
     Barcelona, HELCOM HUB, OSPAR, Annex I);
   * the seagrass members of ``GOOS_EOV`` (JNCC correlation tables, UK MHC v22.04).

   Codes of the 2025 table that do not exist in the classification they are given for, or that mean
   another habitat there, are kept as ``rejected`` rows with the reason (see ``REPORT_2025_ERRORS``).
2. **Proposed by crosswalks** (``status = proposed``): habitats reached from a member through
   ``crosswalks`` (both directions). The target is a ``member`` when the crosswalk says it lies
   within the member, or when its own name names living seagrass; otherwise it is ``partial``
   (e.g. Annex I 1110 *Sandbanks*). Only members are followed further, never partial links, so the
   expansion cannot drift to unrelated habitats.
3. **Proposed by hierarchy and by name**: sub-units of every member, and any habitat of any
   classification whose name names seagrass taxa or seagrass beds and was not reached otherwise
   (``TO REVIEW: found by name only``).

Names that describe plants washed ashore, inland (athalassic) seagrass communities or homonyms
(*Iris halophila*) give ``excluded`` rows. Mixed habitats (seagrass with algae, halophytes,
corals...) give ``partial`` rows.

WP3 decisions (``DECISIONS``, status ``reviewed``): dead *Posidonia* leaves and dead *matte* are
included; associations with *Caulerpa prolifera* (an alga) are excluded.

Items are the seagrass bed types of D3.11 (2025), Appendix Table 3, plus ``seagrass-beds`` for
generic or mixed seagrass habitats; the item of a member is decided from its name (genus named),
or inherited from the member it was reached from.

All proposed rows are proposals of this repository pending WP3 review.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

import pandas as pd

from . import pdftext
from .lists import LISTS, validate_members
from .schema import LIST_ITEMS_COLUMNS, LIST_MEMBERS_COLUMNS, LISTS_COLUMNS

LIST_ID = "EOV_SEAGRASS"

REPORT_2019_GLOB = "*Generating Essential Ocean Variables*.pdf"
REPORT_2025_GLOB = "*D3.11_EOV*.pdf"
SRC_2019 = ("O'Keeffe, E. & Lillis, H., 2019. Generating Essential Ocean Variables. EMODnet Seabed Habitats "
            "(Marine Institute, JNCC)")
SRC_2025 = ("Gonçalves, J., Monteiro, P., O'Keeffe, E., Mcgrath, F., Woods, H., Vasquez, M., Segeat, B., "
            "Laamanen-Nicolas, L., Kallio, N. & Karvinen, V., 2025. Report detailing the construction of the Essential "
            "Ocean Variable data products (updated). EMODnet Seabed Habitats D3.11")

LIST_META = dict(
    list_id=LIST_ID, name="EMODnet Seabed Habitats Seagrass cover EOV composite: habitats used", kind="product",
    version="2026 (D3.03): 2019 and 2025 lists, extended by crosswalks (proposed)",
    authority="EMODnet Seabed Habitats", deliverable="D3.03", scope="European seas and Caribbean",
    source=f"{SRC_2019}, Tables 2, 5, 6; {SRC_2025}, Appendix Table 3; GOOS_EOV seagrass members",
    notes="implements GOOS_EOV seagrass-cover-and-composition/areal-extent")

# item, name, parent, definition, source
ITEMS = [
    ("seagrass", "Seagrass cover (areal extent)", "",
     "Areal extent of seagrass meadows (GOOS EOV Seagrass cover and composition, sub-variable Areal Extent).",
     "GOOS Document No. 322 (August 2026); " + SRC_2019),
    ("zostera-beds", "Zostera beds", "seagrass", "Zostera marina, Zostera noltii, Zostera angustifolia.",
     SRC_2025 + ", Appendix Table 3"),
    ("posidonia-beds", "Posidonia beds", "seagrass", "Posidonia oceanica.", SRC_2025 + ", Appendix Table 3"),
    ("cymodocea-beds", "Cymodocea beds", "seagrass", "Cymodocea nodosa.", SRC_2025 + ", Appendix Table 3"),
    ("ruppia-beds", "Ruppia beds", "seagrass", "Ruppia maritima, Ruppia cirrhosa.", SRC_2025 + ", Appendix Table 3"),
    ("halophila-beds", "Halophila beds", "seagrass",
     "Halophila decipiens, Halophila stipulacea, Halophila baillonis, Halophila engelmannii, Halophila spp.",
     SRC_2025 + ", Appendix Table 3"),
    ("tropical-seagrass-beds", "Tropical seagrass beds (Caribbean)", "seagrass",
     "Thalassia testudinum, Syringodium filiforme, Halodule wrightii, Halodule beaudettei.",
     SRC_2025 + ", Appendix Table 3"),
    ("seagrass-beds", "Seagrass beds, generic or mixed", "seagrass",
     "Habitats named as seagrass beds without one dominant genus, or with several genera.",
     "this repository (habitats of the 2019 and 2025 lists not assigned to one genus)"),
]

# Table 2 of the 2019 report: EUNIS 2007-11 codes (in table order). Tables 5 and 6: OSPAR, Annex I.
REPORT_2019_EUNIS = [
    "A2.131", "A2.61", "A2.611", "A2.6111", "A2.612", "A2.613", "A2.614", "A5.53", "A5.531", "A5.5311",
    "A5.5312", "A5.5313", "A5.53131", "A5.53132", "A5.532", "A5.5321", "A5.5322", "A5.533", "A5.5331",
    "A5.5332", "A5.53321", "A5.53322", "A5.5333", "A5.5334", "A5.534", "A5.5341", "A5.5342", "A5.5343",
    "A5.535", "A5.5351", "A5.5352", "A5.5353", "A5.5354", "A5.545"]
REPORT_2019_OTHER = [  # system, code, name printed in the report, table
    ("OSPAR_TD_2021", "cymodocea-meadows", "Cymodocea meadows", "Table 5"),
    ("OSPAR_TD_2021", "zostera-beds", "Zostera beds", "Table 5"),
    ("ANNEX_I", "1120", "Posidonia Beds", "Table 6"),
]

# Appendix Table 3 of D3.11 (2025): item -> [(system, code as printed, link_type)], plus the regions
# of the table. Ranges ("A5.5351–A5.5354") are expanded with the EUNIS 2012 hierarchy.
REPORT_2025 = {
    "zostera-beds": {"regions": "Atlantic, Arctic, Baltic, Black Sea, Caribbean (coastal lagoons)", "codes": [
        ("EUNIS_M_2019", "MA522", "member"), ("EUNIS_M_2019", "MA623", "member"), ("EUNIS_M_2019", "MB522", "member"),
        ("EUNIS_2012", "A2.611", "member"), ("EUNIS_2012", "A2.613", "member"), ("EUNIS_2012", "A5.533", "member"),
        ("EUNIS_2012", "A5.545", "member"), ("BARCELONA_2006", "III.5.3", "member"),
        ("BARCELONA_2006", "III.5.4", "member"), ("BARCELONA_2019", "MB2.52", "member"),
        ("OSPAR_TD_2021", "zostera-beds", "member"), ("ANNEX_I", "1140", "partial"), ("ANNEX_I", "1110", "partial"),
        ("HELCOM_HUB", "AA-I1B2", "member"), ("HELCOM_HUB", "AA-I1B7", "member"), ("HELCOM_HUB", "AA-H1B7", "member")]},
    "posidonia-beds": {"regions": "Mediterranean", "codes": [
        ("EUNIS_2012", "A5.535", "member"), ("EUNIS_2012", "A5.5351–A5.5354", "member"),
        ("BARCELONA_2006", "III.5.1", "member"), ("BARCELONA_2019", "MB2.54", "member"),
        ("ANNEX_I", "1120", "member")]},
    "cymodocea-beds": {"regions": "Atlantic, Mediterranean", "codes": [
        ("EUNIS_2012", "A5.53", "member"), ("EUNIS_2012", "A5.531–A5.53132", "member"),
        ("BARCELONA_2006", "III.5.2", "member"), ("BARCELONA_2019", "MB2.53", "member"),
        ("OSPAR_TD_2021", "cymodocea-meadows", "member")]},
    "ruppia-beds": {"regions": "Atlantic, Baltic, Mediterranean, Caribbean (lagoon/estuaries)", "codes": [
        ("EUNIS_2012", "A2.61", "member"), ("EUNIS_2012", "A2.614", "member"), ("EUNIS_2012", "A5.534", "member"),
        ("EUNIS_2012", "A5.5341–A5.5343", "member"), ("BARCELONA_2006", "III.5.5", "member"),
        ("BARCELONA_2019", "MB2.56", "member"), ("HELCOM_HUB", "AA-I1B2", "member"),
        ("HELCOM_HUB", "AA-M1B2", "member")]},
    "halophila-beds": {"regions": "Mediterranean, Macaronesian Atlantic, Caribbean", "codes": [
        ("EUNIS_2012", "A5.53", "member"), ("EUNIS_2012", "A5.532", "member"), ("EUNIS_2012", "A5.5321", "member"),
        ("EUNIS_2012", "A5.5322", "member"), ("BARCELONA_2006", "III.5.6", "member"),
        ("BARCELONA_2019", "MB2.55", "member")]},
    "tropical-seagrass-beds": {"regions": "Caribbean Sea", "codes": []},
}
# printed code -> why it is not used (checked against the loaded classifications by the tests)
REPORT_2025_ERRORS = {
    ("BARCELONA_2019", "MB2.52"): "in Barcelona 2019 MB2.52 is 'Reefs on fine sand in very shallow waters' "
                                  "(the report names it 'Zostera spp. meadows'); Zostera is under the "
                                  "'Association with indigenous marine angiosperms' units (MA*.521, MB5.521, MB5.531)",
    ("BARCELONA_2019", "MB2.53"): "in Barcelona 2019 MB2.53 is 'Reefs of Cladocora caespitosa' (the report names "
                                  "it 'Cymodocea nodosa meadows'): using it would put coral in the seagrass product",
    ("BARCELONA_2019", "MB2.55"): "not a Barcelona 2019 code (the report names it 'Halophila stipulacea "
                                  "meadows'); Halophila is under MA*.522, MB5.522, MB5.532",
    ("BARCELONA_2019", "MB2.56"): "not a Barcelona 2019 code (the report names it 'Ruppia spp. meadows')",
    ("BARCELONA_2006", "III.5.2"): "not a Barcelona 2006 code (III.5 is Posidonia oceanica meadows only); "
                                   "Cymodocea nodosa is III.2.2.1 and III.2.3.4",
    ("BARCELONA_2006", "III.5.3"): "not a Barcelona 2006 code; Zostera noltii is III.1.1.4 and III.2.3.5",
    ("BARCELONA_2006", "III.5.4"): "not a Barcelona 2006 code; Zostera marina is III.1.1.5",
    ("BARCELONA_2006", "III.5.5"): "not a Barcelona 2006 code; Ruppia is III.1.1.1",
    ("BARCELONA_2006", "III.5.6"): "not a Barcelona 2006 code; Halophila stipulacea is III.2.2.2",
}

GENERA = {  # item -> pattern on habitat names (English, French)
    "posidonia-beds": r"posidoni",
    "cymodocea-beds": r"cymodoce",
    "halophila-beds": r"(?<!iris )halophila",
    "ruppia-beds": r"ruppia|zannichellia",
    "zostera-beds": r"zostera|eelgrass|eel-grass",
}
TROPICAL = r"thalassia testudinum|syringodium|halodule|tropical sea-?grass|tropical atlantic seagrass|subtropical hydrocharit"
SEAGRASS_NAME = re.compile(
    r"zostera|posidoni|cymodoce|halophila|ruppia|zannichellia|thalassia|syringodium|halodule|sea-?grass|eel-?grass|"
    r"herbier|marine angiosperm|aquatic angiosperm|angiosperm communit|marine phanerogam", re.I)
EXCLUDED_NAME = re.compile(r"washed ashore|iris halophila|athalassic|deposit of dead", re.I)

# WP3 decisions (Pedro Monteiro, CCMAR, 2026-11-25): name pattern -> (link_type, reason). They apply to
# every row of the habitat (published or proposed), which becomes ``reviewed``.
DECIDED_BY, DECIDED_ON = "Pedro Monteiro (WP3, CCMAR)", "2026-11-25"
DECISIONS = [
    (re.compile(r"association with \W*caulerpa prolifera", re.I), "excluded",
     "WP3 decision: Caulerpa prolifera is an alga, not a seagrass; associations with it are left out"),
    (re.compile(r"dead leaves|dead\W+(?:«\s*)?mattes?\b", re.I), "member",
     "WP3 decision: dead Posidonia leaves and dead matte are included"),
]
PARTIAL_NAME = re.compile(
    r"halophyte|algal|algae|algues|coraux|coral|gorgon|caulerpa spp|or caulerpa|angiosperm communit|"
    r"dominated by aquatic angiosperms|rhizomatous", re.I)
# sub-trees not followed from a member (the parent is mixed)
CARIB_SYSTEMS = {"CARIB_MARTINIQUE_2022", "FR_APHN_ANTILLES", "ALLEN_CORAL_ATLAS_BENTHIC"}


def item_for(name: str, system: str = "", default: str = "seagrass-beds") -> str:
    """Seagrass item from a habitat name: one genus named -> its bed type; tropical taxa or a Caribbean
    classification -> tropical beds; Posidonia wins over the genera associated with it."""
    n = name.lower() if isinstance(name, str) else ""
    n = re.sub(r"\(?other than \w+\)?", "", n)
    if (system in CARIB_SYSTEMS and SEAGRASS_NAME.search(n)) or (re.search(TROPICAL, n) and "temperate" not in n):
        return "tropical-seagrass-beds"
    hits = [it for it, p in GENERA.items() if re.search(p, n)]
    if "posidonia-beds" in hits:
        return "posidonia-beds"
    if len(hits) == 1:
        return hits[0]
    return "seagrass-beds" if hits or SEAGRASS_NAME.search(n) else default


def decision_for(name: str) -> tuple[str, str] | None:
    n = name if isinstance(name, str) else ""
    for pattern, link, why in DECISIONS:
        if pattern.search(n):
            if link == "member" and re.search(r"caulerpa spp|or caulerpa|cymodocea", n, re.I):
                return None   # living seagrass or algae on dead matte: mixed, left to the name rules
            return link, why
    return None


def link_for_name(name: str) -> tuple[str, str]:
    """(link_type, reason) from the habitat name alone (WP3 decisions first)."""
    n = name if isinstance(name, str) else ""
    d = decision_for(n)
    if d:
        return d
    if EXCLUDED_NAME.search(n):
        return "excluded", "plants washed ashore, inland or homonym (not living marine seagrass)"
    if re.search(r"dead\W+(?:«\s*)?mattes?\b", n, re.I):
        return "partial", "mixed habitat (seagrass or algae on dead Posidonia matte)"
    if PARTIAL_NAME.search(n):
        return "partial", "mixed habitat (seagrass with algae, halophytes or other communities)"
    return "member", ""


def apply_decisions(members: pd.DataFrame, habitats: pd.DataFrame) -> pd.DataFrame:
    """Set the WP3 decisions on every row of the habitats they concern (status ``reviewed``)."""
    names = dict(zip(zip(habitats.system, habitats.code), habitats.name))
    m = members.copy()
    for i, r in m.iterrows():
        d = decision_for(names.get((r.system, r.code), ""))
        if d and r.status != "rejected":
            m.at[i, "link_type"], m.at[i, "status"] = d[0], "reviewed"
            m.at[i, "decided_by"], m.at[i, "decided_on"] = DECIDED_BY, DECIDED_ON
            notes = re.sub(r"(; )?TO REVIEW: [^;]*(; the 2019 layer[^;]*)?", "", str(r.notes or "")).strip("; ")
            m.at[i, "notes"] = "; ".join(x for x in [notes, d[1]] if x)
    return m


def _norm(s: str) -> str:
    return " ".join(s.replace("–", "-").split())


def _expand(code: str, hab: pd.DataFrame, system: str) -> list[str]:
    """'A5.5351–A5.5354' -> the EUNIS 2012 codes from the first to the last in code order."""
    if "–" not in code:
        return [code.replace("AA-", "AA.") if system == "HELCOM_HUB" else code]
    first, last = code.split("–")
    codes = sorted(hab.loc[hab.system == system, "code"])
    lo, hi = codes.index(first), codes.index(last)
    return codes[lo:hi + 1]


def report_text(reports: Path, glob: str, layout: bool = True) -> str:
    pdf = sorted(reports.glob(glob))
    if not pdf:
        raise FileNotFoundError(f"{reports}/{glob}")
    return _norm("\n".join(pdftext.pdf_to_lines(pdf[0], layout=layout)))


def _row(item, system, code, link_type, status, rel, source, notes, today):
    proposed = status in {"proposed", "rejected"}
    return {"list_id": LIST_ID, "item": item, "region": "", "zone": "", "system": system, "code": code,
            "link_type": link_type, "status": status, "source_relationship": rel,
            "decided_by": "proposal (repository), pending WP3 review" if proposed else "",
            "decided_on": today if proposed else "", "source": source, "notes": notes}


def published_members(habitats: pd.DataFrame, members: pd.DataFrame, today: str) -> pd.DataFrame:
    names = {(s, c): n for s, c, n in zip(habitats.system, habitats.code, habitats.name)}
    rows = []
    for code in REPORT_2019_EUNIS:
        name = names.get(("EUNIS_2012", code), "")
        notes = ""
        rows.append(_row(item_for(name), "EUNIS_2012", code, "member", "published", "listed",
                         f"{SRC_2019}, Table 2", notes, today))
    for system, code, printed, table in REPORT_2019_OTHER:
        rows.append(_row(item_for(printed), system, code, "member", "published", "listed",
                         f"{SRC_2019}, {table}", f"printed: {printed}", today))
    for item, spec in REPORT_2025.items():
        for system, printed, link in spec["codes"]:
            src = f"{SRC_2025}, Appendix Table 3"
            for code in _expand(printed, habitats, system):
                notes = f"regions (D3.11): {spec['regions']}"
                if printed != code:
                    notes += f"; printed: {printed}"
                if (system, printed) in REPORT_2025_ERRORS:
                    rows.append(_row(item, system, code, "excluded", "rejected", "listed", src,
                                     f"{notes}; code not used: {REPORT_2025_ERRORS[(system, printed)]}", today))
                    continue
                rows.append(_row(item, system, code, link, "published", "listed", src, notes, today))
    goos = members[(members.list_id == "GOOS_EOV") & (members.item == "seagrass-cover-and-composition")]
    for _, r in goos.iterrows():
        name = names.get((r.system, r.code), "")
        rows.append(_row(item_for(name, r.system), r.system, r.code, r.link_type, r.status,
                         f"GOOS_EOV member ({r.source_relationship})", r.source,
                         f"via GOOS_EOV seagrass-cover-and-composition; {r.notes}".rstrip("; "), today))
    return pd.DataFrame(rows, columns=LIST_MEMBERS_COLUMNS)


def _contained(rel: str, seed_is_from: bool) -> bool:
    """True when the crosswalk says the target lies within the seed (relationship read from ``from``)."""
    return rel == "=" or (rel == ">" if seed_is_from else rel == "<")


def proposed_members(seeds: pd.DataFrame, habitats: pd.DataFrame, crosswalks: pd.DataFrame,
                     today: str) -> pd.DataFrame:
    classif = set(habitats.system) - set(LISTS) - {LIST_ID}
    cw = crosswalks[crosswalks.from_system.isin(classif) & crosswalks.to_system.isin(classif)]
    names = {(s, c): n for s, c, n in zip(habitats.system, habitats.code, habitats.name)}
    known = set(names)
    done = set(zip(seeds.system, seeds.code))
    rows = []
    # 1. crosswalks, followed only from members
    frontier = [(s, c, it) for s, c, it, lt, st in zip(seeds.system, seeds.code, seeds["item"], seeds.link_type,
                                                       seeds.status) if lt == "member" and st != "rejected"]
    by_from = {k: g for k, g in cw.groupby(["from_system", "from_code"])}
    by_to = {k: g for k, g in cw.groupby(["to_system", "to_code"])}
    while frontier:
        nxt = []
        for s, c, it in frontier:
            for side, g in (("from", by_from.get((s, c))), ("to", by_to.get((s, c)))):
                if g is None:
                    continue
                other = "to" if side == "from" else "from"
                for _, r in g.iterrows():
                    ts, tc = r[f"{other}_system"], r[f"{other}_code"]
                    if (ts, tc) in done or (ts, tc) not in known:
                        continue
                    name = names[(ts, tc)]
                    link, why = link_for_name(name)
                    inside = _contained(r.relationship, side == "from")
                    if link == "member" and not inside and not SEAGRASS_NAME.search(name):
                        link, why = "partial", "broader than or overlapping the seagrass habitat it is linked to"
                    done.add((ts, tc))
                    notes = f"via {s} {c} (crosswalk '{r.relationship}', {r.source})"
                    if why:
                        notes += f"; {why}"
                    rows.append(_row(item_for(name, ts, it), ts, tc, link, "proposed", r.relationship,
                                     "crosswalks.csv", notes, today))
                    if link == "member":
                        nxt.append((ts, tc, item_for(name, ts, it)))
        frontier = nxt
    # 2. sub-units of members (parent_code, or "parent/child" codes)
    all_members = pd.concat([seeds, pd.DataFrame(rows, columns=LIST_MEMBERS_COLUMNS)], ignore_index=True)
    children: dict[tuple[str, str], list[str]] = {}
    for s, c, p in zip(habitats.system, habitats.code, habitats.parent_code):
        parent = p if isinstance(p, str) and p else (c.rsplit("/", 1)[0] if "/" in c else None)
        if parent:
            children.setdefault((s, parent), []).append(c)
    stack = [(s, c, it) for s, c, it, lt, st in zip(all_members.system, all_members.code, all_members["item"],
                                                    all_members.link_type, all_members.status)
             if lt == "member" and st != "rejected"]
    while stack:
        s, c, it = stack.pop()
        for k in children.get((s, c), []):
            if (s, k) in done:
                continue
            done.add((s, k))
            name = names[(s, k)]
            link, why = link_for_name(name)
            notes = f"sub-unit of {s} {c}" + (f"; {why}" if why else "")
            rows.append(_row(item_for(name, s, it), s, k, link, "proposed", "sub-unit", "habitats.csv (hierarchy)",
                             notes, today))
            if link == "member":
                stack.append((s, k, item_for(name, s, it)))
    # a partial link only because the crosswalk is loose, under a member parent, is a member
    member_keys = {(r["system"], r["code"]) for r in rows if r["link_type"] == "member"} | \
        {(s, c) for s, c, lt, st in zip(seeds.system, seeds.code, seeds.link_type, seeds.status)
         if lt == "member" and st != "rejected"}
    parent_of = {(s, k): c for (s, c), ks in children.items() for k in ks}
    for r in rows:
        par = parent_of.get((r["system"], r["code"]))
        if r["link_type"] == "partial" and "broader than or overlapping" in r["notes"] and \
                (r["system"], par) in member_keys:
            r["link_type"] = "member"
            r["notes"] = r["notes"].replace("broader than or overlapping the seagrass habitat it is linked to",
                                            f"sub-unit of member {r['system']} {par}")
    # 3. names only
    for s, c in sorted(known - done):
        if s not in classif:
            continue
        name = names[(s, c)]
        if not SEAGRASS_NAME.search(name):
            continue
        link, why = link_for_name(name)
        notes = "TO REVIEW: found by name only (no crosswalk or parent in the list)" + (f"; {why}" if why else "")
        rows.append(_row(item_for(name, s), s, c, link, "proposed", "name", "habitats.csv (name)", notes, today))
        done.add((s, c))
    return pd.DataFrame(rows, columns=LIST_MEMBERS_COLUMNS)


def items_table() -> pd.DataFrame:
    return pd.DataFrame([{"list_id": LIST_ID, "item": i, "name": n, "level": 1 if not p else 2, "parent_item": p,
                          "definition": d, "attributes": "", "source": s, "notes": ""} for i, n, p, d, s in ITEMS],
                        columns=LIST_ITEMS_COLUMNS)


def build(habitats: pd.DataFrame, crosswalks: pd.DataFrame, members: pd.DataFrame, today: str | None = None
          ) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Return (lists row, list_items rows, list_members rows) of ``EOV_SEAGRASS``."""
    today = today or date.today().isoformat()
    seeds = published_members(habitats, members, today)
    prop = proposed_members(seeds, habitats, crosswalks, today)
    lists_row = {**LIST_META, "accessed": today, "status": "loaded"}
    return lists_row, items_table(), apply_decisions(pd.concat([seeds, prop], ignore_index=True), habitats)


RANK = {("member", "reviewed"): -1, ("excluded", "reviewed"): -1, ("partial", "reviewed"): -1,
        ("member", "published"): 0, ("member", "proposed"): 1,
        ("partial", "published"): 2, ("partial", "proposed"): 3,
        ("excluded", "proposed"): 4, ("excluded", "published"): 4, ("excluded", "rejected"): 5}


def filter_table(members: pd.DataFrame, habitats: pd.DataFrame) -> pd.DataFrame:
    """One row per (system, code): the link used by the filter (best of its rows), the item, the
    sources and what to review. ``use``:

    * ``yes``: member, all its polygons go into the product;
    * ``partial``: mixed habitat that names seagrass (seagrass with algae, halophytes...);
    * ``broader``: habitat that contains seagrass among others (e.g. Annex I 1110 Sandbanks);
    * ``no``: excluded or rejected (dead plants, wrong codes in a report...).

    How ``partial`` and ``broader`` polygons are used (extra criterion or left out) is a WP3 decision."""
    m = members[members.list_id == LIST_ID].copy()
    m["rank"] = [RANK.get((lt, st), 6) for lt, st in zip(m.link_type, m.status)]
    names = habitats.set_index(["system", "code"])["name"]
    out = []
    for (s, c), g in m.groupby(["system", "code"], sort=True):
        g = g.sort_values("rank")
        best = g.iloc[0]
        name = names.get((s, c), "")
        review = "; ".join(sorted({x.split("TO REVIEW: ", 1)[1] for x in g.notes.fillna("") if "TO REVIEW: " in x}))
        if best.link_type == "member" and (g.link_type == "excluded").any():
            review = "; ".join(x for x in [review, "listed as member and as excluded"] if x)
        name = name if isinstance(name, str) else ""
        use = {"member": "yes", "partial": "partial" if SEAGRASS_NAME.search(name) else "broader"}.get(
            best.link_type, "no")
        if use == "yes" and best.status != "reviewed" and link_for_name(name)[0] == "excluded":
            use = "no"
            review = "; ".join(x for x in [review, "listed as member, but the name says excluded: left out until "
                                                   "WP3 decides"] if x)
        out.append({"system": s, "code": c, "name": name, "item": item_for(name, s, best["item"]),
                    "link_type": best.link_type, "status": best.status, "use": use,
                    "sources": "; ".join(sorted(set(g.source))), "n_rows": len(g), "review": review,
                    "notes": best.notes if isinstance(best.notes, str) else ""})
    f = pd.DataFrame(out)
    f["_o"] = f.use.map({"yes": 0, "partial": 1, "broader": 2, "no": 3})
    return f.sort_values(["_o", "system", "code"]).drop(columns="_o").reset_index(drop=True)


def update_processed(processed: Path, today: str | None = None) -> dict[str, pd.DataFrame]:
    """Add (or replace) ``EOV_SEAGRASS`` in the tables of ``processed`` and write
    ``eov_seagrass_filter.csv``. Needs only the processed tables (no source files)."""
    rd = lambda n: pd.read_csv(processed / n, dtype=str, keep_default_na=False)
    habitats, crosswalks = rd("habitats.csv"), rd("crosswalks.csv")
    lists_df, items, members = rd("lists.csv"), rd("list_items.csv"), rd("list_members.csv")
    lists_df, items, members = (lists_df[lists_df.list_id != LIST_ID], items[items.list_id != LIST_ID],
                                members[members.list_id != LIST_ID])
    row, new_items, new_members = build(habitats, crosswalks, members, today)
    lists_df = pd.concat([lists_df, pd.DataFrame([row], columns=LISTS_COLUMNS)], ignore_index=True)
    items = pd.concat([items, new_items.astype(str).replace("nan", "")], ignore_index=True)
    members = pd.concat([members, new_members.fillna("")], ignore_index=True)
    members = validate_members(members, items, habitats)
    filt = filter_table(members, habitats)
    lists_df.to_csv(processed / "lists.csv", index=False)
    items.to_csv(processed / "list_items.csv", index=False)
    members.to_csv(processed / "list_members.csv", index=False)
    filt.to_csv(processed / "eov_seagrass_filter.csv", index=False)
    return {"lists": lists_df, "list_items": items, "list_members": members, "filter": filt}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Add the EOV_SEAGRASS list to the processed tables.")
    p.add_argument("--processed", type=Path, default=Path("data/processed"))
    a = p.parse_args(argv)
    t = update_processed(a.processed)
    m = t["list_members"][t["list_members"].list_id == LIST_ID]
    print(m.groupby(["status", "link_type"]).size().to_string())
    f = t["filter"]
    print(f.groupby(["use", "system"]).size().to_string())
    print(f"filter: {len(f)} habitats -> {a.processed / 'eov_seagrass_filter.csv'}; "
          f"to review: {(f.review != '').sum()}")


if __name__ == "__main__":
    main()
