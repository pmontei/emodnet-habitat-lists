"""OSPAR List of Threatened and/or Declining Habitats (North-East Atlantic).

System produced
---------------
``OSPAR_TD_2021``
    The 18 habitats of Part II of OSPAR Agreement 2008-06 (List, amended 2021), with the sub-types
    described in OSPAR Agreement 2008-07 (Descriptions, revised 2021).

OSPAR habitats have **no official codes**. Codes used here are the habitat slugs of the OSPAR
website (also used as folder names in the sources), e.g. ``zostera-beds``; sub-types are
``<habitat>/<sub-type>``. The sub-type numbers printed in Agreement 2008-07 (8.1, 8.2, 9.1, 9.2)
are kept in ``notes``.

Crosswalks produced
-------------------
* ``OSPAR_TD_2021`` -> ``EUNIS_2012`` and ``UK_MNCR_0405``: codes given in Agreement 2008-07
  (per-habitat extracts ``*_definition.pdf``). The EUNIS codes there refer to the February 2004
  version of EUNIS; they are compared with ``EUNIS_2012`` (codes not found are flagged).
* ``OSPAR_TD_2021`` (kelp forest) -> ``EUNIS_2012``: indicative list, Appendix I of the kelp
  forest case report (OSPAR publication 787, 2021).
* ``OSPAR_TD_2021`` (Haploops habitat) -> ``EUNIS_2012`` / ``HELCOM_HUB``: Agreement 2008-07 text.
* ``OSPAR_TD_2021`` -> ``EMODNET_OSPAR2025``: the ``habtype`` / ``habsubtype`` values used in the
  EMODnet Seabed Habitats OSPAR habitats dataset (WFS ``emodnet_view:ospar2025_points`` and
  ``emodnet_view:ospar2025_polygons``).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ..pdftext import pdf_to_lines
from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS

FOLDER = "4.OSPAR"
SRC_LIST = "OSPAR Agreement 2008-06 (List of Threatened and/or Declining Species and Habitats, amended 2021), Part II - Habitats"
SRC_DESC = "OSPAR Agreement 2008-07 (Descriptions of habitats on the OSPAR List, revised 2021)"
SRC_KELP = "OSPAR 2021, Case report for kelp forest habitat (publication 787), Appendix I"
SRC_EMODNET = (
    "EMODnet Seabed Habitats WFS emodnet_view:ospar2025_points / ospar2025_polygons, "
    "distinct habtype/habsubtype values (EMODnet_OSPAR2025_habtype_habsubtype_values.csv)"
)

# Part II of Agreement 2008-06 (2021). Transcribed from the official PDF, which has no text layer.
# code, name, regions where it occurs, regions where under threat and/or in decline, footnote
LIST_2021 = [
    ("carbonate-mounds", "Carbonate mounds", "I, V", "V", "To be confirmed in the light of further survey work being undertaken by Ireland"),
    ("coral-gardens", "Coral gardens", "I, II, III, IV, V", "All where they occur", ""),
    ("cymodocea-meadows", "Cymodocea meadows", "IV", "All where they occur", ""),
    ("deep-sea-sponge-aggregations", "Deep-sea sponge aggregations", "I, III, IV, V", "All where they occur", ""),
    ("haploops", "Haploops habitat", "II, IV", "II", "Added in 2021"),
    ("intertidal-mytilus-edulis-beds", "Intertidal Mytilus edulis beds on mixed and sandy sediments", "II, III", "All where they occur", ""),
    ("intertidal-mudflats", "Intertidal mudflats", "I, II, III, IV", "All where they occur", ""),
    ("kelp-forest", "Kelp forests", "All", "II, III, IV", "Added in 2021. Defined by specific species of kelp in decline in specific Regions as identified in the case report"),
    ("littoral-chalk-communities", "Littoral chalk communities", "II", "All where they occur", ""),
    ("lophelia-pertusa-reefs", "Lophelia pertusa reefs", "All", "All where they occur", "Accepted species name (WoRMS): Desmophyllum pertusum"),
    ("maerl-beds", "Maerl beds", "All", "III", ""),
    ("modiolus-modiolus-beds", "Modiolus modiolus beds", "All", "All where they occur", "Named 'Modiolus modiolus horse mussel beds' in Agreement 2008-07"),
    ("oceanic-ridges-with-hydrothermal-vents", "Oceanic ridges with hydrothermal vents/fields", "I, V", "V", ""),
    ("ostrea-edulis-beds", "Ostrea edulis beds", "II, III, IV", "All where they occur", ""),
    ("sabellaria-spinulosa-reefs", "Sabellaria spinulosa reefs", "All", "II, III", ""),
    ("seamounts", "Seamounts", "I, IV, V", "All where they occur", ""),
    ("sea-pen-burrowing-megafauna", "Sea-pen and burrowing megafauna communities", "I, II, III, IV", "II, III", ""),
    ("zostera-beds", "Zostera beds", "I, II, III, IV", "All where they occur", ""),
]

# Sub-types described in Agreement 2008-07
SUBTYPES = [
    ("zostera-beds/zostera-marina-beds", "Zostera marina beds", "zostera-beds", "8.1 in Agreement 2008-07"),
    ("zostera-beds/zostera-noltii-beds", "Zostera noltii beds", "zostera-beds", "8.2 in Agreement 2008-07"),
    ("intertidal-mudflats/marine-intertidal-mudflats", "Marine intertidal mudflats", "intertidal-mudflats", "9.1 in Agreement 2008-07"),
    ("intertidal-mudflats/estuarine-intertidal-mudflats", "Estuarine intertidal mudflats", "intertidal-mudflats", "9.2 in Agreement 2008-07"),
    ("sabellaria-spinulosa-reefs/on-rock", "Sabellaria spinulosa reefs on rock", "sabellaria-spinulosa-reefs", "sub-type in Agreement 2008-07 (not numbered)"),
    ("sabellaria-spinulosa-reefs/on-mixed-sediment", "Sabellaria spinulosa reefs on mixed (sediment) substrata", "sabellaria-spinulosa-reefs", "sub-type in Agreement 2008-07 (not numbered)"),
]


def habitats() -> pd.DataFrame:
    rows = []
    for code, name, occurs, threat, note in LIST_2021:
        notes = f"OSPAR Regions where it occurs: {occurs}; under threat and/or in decline: {threat}"
        if note:
            notes += f". {note}"
        rows.append({"code": code, "name": name, "level": 1, "parent_code": None, "notes": notes, "source": SRC_LIST})
    for code, name, parent, note in SUBTYPES:
        rows.append({"code": code, "name": name, "level": 2, "parent_code": parent, "notes": note, "source": SRC_DESC})
    df = pd.DataFrame(rows)
    df.insert(0, "system", "OSPAR_TD_2021")
    df["level"] = df["level"].astype("Int64")
    df["realm"] = "marine"
    df["group"] = None
    df["description"] = None
    return df[HABITATS_COLUMNS]


# ---------------------------------------------------------------------------------------------
# Crosswalks from Agreement 2008-07 (per-habitat extracts)
# ---------------------------------------------------------------------------------------------
EUNIS_TOKEN = re.compile(r"\b([A-J][1-9](?:\.[0-9A-Z]+)?)\b")
UK_TOKEN = re.compile(r"\b((?:LS|LR|SS|CR|IR)\.[A-Za-z][A-Za-z0-9.]*[A-Za-z0-9])")
EUNIS_QUALIFIER = {
    "coral-gardens": "occurs within (EUNIS deep-sea types)",
    "littoral-chalk-communities": "various including",
}


def crosswalk_definitions(sources: Path) -> pd.DataFrame:
    rows = []
    for code, *_ in LIST_2021:
        pdfs = sorted((sources / FOLDER / code).glob("*_definition.pdf"))
        if not pdfs:
            continue
        text = " ".join(l.strip() for l in pdf_to_lines(pdfs[0], layout=False))
        uk_at = text.find("National Marine Habitat Classification")
        head = text[: uk_at if uk_at > 0 else 600]
        if code == "coral-gardens":
            eunis = re.findall(r"\b(A6\.\d)\b", head)
        else:
            m = re.search(r"EUNIS [Cc]ode\s*:\s*(.*)", head)
            eunis = EUNIS_TOKEN.findall(m.group(1)) if m else []
        uk_txt = text[uk_at: uk_at + 400] if uk_at > 0 else ""
        uk_txt = uk_txt.split(":", 1)[1] if ":" in uk_txt else ""
        uk = [] if uk_txt.strip().lower().startswith("not defined") else UK_TOKEN.findall(uk_txt)
        src = f"{SRC_DESC}, extract {pdfs[0].name}"
        for e in dict.fromkeys(eunis):
            rows.append({"from_system": "OSPAR_TD_2021", "from_code": code, "to_system": "EUNIS_2012",
                         "to_code": e, "relationship": EUNIS_QUALIFIER.get(code, "unspecified"),
                         "source": src, "notes": "EUNIS code as given in Agreement 2008-07 (EUNIS version of February 2004)"})
        for u in dict.fromkeys(uk):
            fixed = UK_0405_FIXES.get(u, u)
            rows.append({"from_system": "OSPAR_TD_2021", "from_code": code, "to_system": "UK_MNCR_0405",
                         "to_code": fixed, "relationship": "unspecified", "source": src,
                         "notes": f"printed as '{u}' in Agreement 2008-07; v04.05 code is '{fixed}'"
                         if fixed != u else ""})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


# UK v04.05 codes as printed in Agreement 2008-07 that are not v04.05 codes (checked against the
# v04.05 units named in the JNCC correlation tables)
UK_0405_FIXES = {
    "LS.LMX.LMus.Myt.Mx": "LS.LBR.LMus.Myt.Mx",   # Mytilus edulis beds on littoral mixed substrata
    "LS.LMX.LMus.Myt.Sa": "LS.LBR.LMus.Myt.Sa",   # Mytilus edulis beds on littoral sand
    "LS.LMP.LSgr": "LS.LMp.LSgr",                 # Seagrass beds on littoral sediments
    "SS.SMP.SSgr": "SS.SMp.SSgr",                 # Sublittoral seagrass beds
}


def crosswalk_kelp(sources: Path) -> pd.DataFrame:
    pdfs = sorted((sources / FOLDER / "kelp-forest").glob("p00787*case_report*.pdf"))
    if not pdfs:
        return pd.DataFrame(columns=CROSSWALKS_COLUMNS)
    lines = pdf_to_lines(pdfs[0], layout=False)
    on, codes = False, []
    for ln in lines:
        s = ln.strip()
        if s.startswith("Appendix I. Corresponding EUNIS habitats units") and codes == [] and on is False:
            on = True  # first occurrence is the table of contents; reset below if no codes follow
            continue
        if on and s.startswith("Appendix II"):
            if codes:
                break
            on = False
            continue
        if on:
            m = re.match(r"^(A\d\.\d{3,5})\s+\S", s)
            if m:
                codes.append(m.group(1))
    rows = [{"from_system": "OSPAR_TD_2021", "from_code": "kelp-forest", "to_system": "EUNIS_2012", "to_code": c,
             "relationship": "indicative", "source": SRC_KELP,
             "notes": "EUNIS 2012 units that can correspond to kelp forest (expert list)"} for c in dict.fromkeys(codes)]
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


def crosswalk_haploops() -> pd.DataFrame:
    src = SRC_DESC + ", Haploops habitat"
    rows = [
        {"from_system": "OSPAR_TD_2021", "from_code": "haploops", "to_system": "EUNIS_2012", "to_code": c,
         "relationship": "found in", "source": src,
         "notes": "The habitat does not correspond directly to any EUNIS (2004) level 4 habitat; it is found in these"}
        for c in ("A5.37", "A5.36", "A5.34")
    ]
    rows.append({"from_system": "OSPAR_TD_2021", "from_code": "haploops", "to_system": "HELCOM_HUB",
                 "to_code": "AB.H1I2", "relationship": "unspecified", "source": src,
                 "notes": "Printed as 'AB.H1l2' (lower-case L) in Agreement 2008-07; HUB code is AB.H1I2"})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


# ---------------------------------------------------------------------------------------------
# EMODnet names
# ---------------------------------------------------------------------------------------------
EMODNET_HABTYPE = {
    "Carbonate mounds": "carbonate-mounds",
    "Coral gardens": "coral-gardens",
    "Deep-sea sponge aggregations": "deep-sea-sponge-aggregations",
    "Haploops": "haploops",
    "Intertidal Mytilus edulis beds on mixed and sandy sediments": "intertidal-mytilus-edulis-beds",
    "Intertidal mudflats": "intertidal-mudflats",
    "Kelp forests": "kelp-forest",
    "Littoral chalk communities": "littoral-chalk-communities",
    "Lophelia pertusa reefs": "lophelia-pertusa-reefs",
    "Maerl beds": "maerl-beds",
    "Modiolus modiolus horse mussel beds": "modiolus-modiolus-beds",
    "Oceanic ridges with hydrothermal vents/fields": "oceanic-ridges-with-hydrothermal-vents",
    "Ostrea edulis beds": "ostrea-edulis-beds",
    "Sabellaria spinulosa reefs": "sabellaria-spinulosa-reefs",
    "Sea-pen and burrowing megafauna communities": "sea-pen-burrowing-megafauna",
    "Seamounts": "seamounts",
    "Zostera beds": "zostera-beds",
}
EMODNET_HABSUBTYPE = {
    "Zostera marina beds": ("zostera-beds/zostera-marina-beds", "="),
    "Zostera noltii beds": ("zostera-beds/zostera-noltii-beds", "="),
    "Zostera noltei beds": ("zostera-beds/zostera-noltii-beds", "="),
    "Marine intertidal mudflats": ("intertidal-mudflats/marine-intertidal-mudflats", "="),
    "Estuarine intertidal mudflats": ("intertidal-mudflats/estuarine-intertidal-mudflats", "="),
    "Sabellaria spinulosa reefs on rock": ("sabellaria-spinulosa-reefs/on-rock", "="),
    "Sabellaria spinulosa reefs on mixed (sediment) substrata": ("sabellaria-spinulosa-reefs/on-mixed-sediment", "="),
}
NO_SUBTYPE = {"Unknown", "Not Applicable", "Not applicable", ""}


def crosswalk_emodnet(sources: Path) -> pd.DataFrame:
    f = sources / FOLDER / "EMODnet_OSPAR2025_habtype_habsubtype_values.csv"
    if not f.is_file():
        return pd.DataFrame(columns=CROSSWALKS_COLUMNS)
    v = pd.read_csv(f, dtype=str, keep_default_na=False)
    v["n_features"] = v["n_features"].astype(int)
    rows = []
    for ht, g in v.groupby("habtype"):
        n = g.groupby("layer")["n_features"].sum().to_dict()
        rows.append({"from_system": "OSPAR_TD_2021", "from_code": EMODNET_HABTYPE.get(ht, "?"),
                     "to_system": "EMODNET_OSPAR2025", "to_code": f"habtype={ht}", "relationship": "=",
                     "source": SRC_EMODNET,
                     "notes": f"features: points {n.get('ospar2025_points', 0)}, polygons {n.get('ospar2025_polygons', 0)}"})
        for st, gs in g.groupby("habsubtype"):
            if st in NO_SUBTYPE:
                continue
            n = gs.groupby("layer")["n_features"].sum().to_dict()
            target, rel = EMODNET_HABSUBTYPE.get(st, (EMODNET_HABTYPE.get(ht, "?"), ">"))
            note = f"features: points {n.get('ospar2025_points', 0)}, polygons {n.get('ospar2025_polygons', 0)}"
            if st == "Zostera noltei beds":
                note += "; spelling variant of 'Zostera noltii beds' in the dataset"
            if rel == ">":
                note += "; EMODnet sub-type not defined in Agreement 2008-07 (OSPAR habitat is broader)"
            rows.append({"from_system": "OSPAR_TD_2021", "from_code": target, "to_system": "EMODNET_OSPAR2025",
                         "to_code": f"habtype={ht} | habsubtype={st}", "relationship": rel,
                         "source": SRC_EMODNET, "notes": note})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


def crosswalks(sources: Path) -> pd.DataFrame:
    return pd.concat(
        [crosswalk_definitions(sources), crosswalk_kelp(sources), crosswalk_haploops(), crosswalk_emodnet(sources)],
        ignore_index=True,
    )
