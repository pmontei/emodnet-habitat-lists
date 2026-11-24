"""Nature Restoration Regulation (EU) 2024/1991, Annex II: marine habitat types and groups.

System produced
---------------
(Parsed as a system, then stored by ``lists.split`` as the list ``NRL_2024_MARINE``: the units below become
``list_items`` and the crosswalks become ``list_members``.)

``NRL_2024``
    The seven groups of marine habitat types of Annex II (level 1, codes ``G1`` ... ``G7``) and,
    within each group, the marine regions under which the habitat types are listed (level 2,
    e.g. ``G1-ATL`` "Seagrass beds – Atlantic"). The habitat types themselves are EUNIS 2022
    habitats, so they are not repeated as ``NRL_2024`` rows: they are linked through crosswalks.

Crosswalks produced
-------------------
* ``NRL_2024 -> EUNIS_M_2022`` (``>``: the group/region contains the EUNIS habitat type), one row
  per EUNIS code listed in Annex II. A habitat type can be listed under several groups.
* ``EUNIS_M_2022 -> ANNEX_I`` (``unspecified``): the "Related habitat type code as referred to in
  Annex I to Directive 92/43/EEC" column, which the Regulation takes from the EEA 2021 crosswalk.

Names in Annex II differ slightly from the EEA file (British spelling, punctuation); the Annex II
name is kept in ``notes``. Codes with a Greek letter (e.g. ``MB151α``) are EUNIS codes as printed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS

FOLDER = "9.Restauration law"
REGULATION_GLOB = "01_2024_*2024-1991*.pdf"
SRC = ("Regulation (EU) 2024/1991 of 24 June 2024 on nature restoration (OJ L, 2024/1991, 29.7.2024), Annex II "
       "'Marine ecosystems - habitat types and groups of habitat types referred to in Article 5(1) and (2)'")
REGIONS = {"Atlantic": "ATL", "Baltic Sea": "BAL", "Black Sea": "BLS", "Mediterranean Sea": "MED"}

_GROUP = re.compile(r"^\s*([1-7])\.\s+Group\s+\1:\s+(.+?)\s*$")
_REGION = re.compile(rf"^\s*({'|'.join(REGIONS)})\s*$")
_ROW = re.compile(r"^\s*(M[A-H][0-9A-Z]{1,6}\S?)\s{2,}(\S.*?)(?:\s+((?:\d{4};\s*)*\d{4}))?\s*$")
_NOISE = re.compile(r"EUNIS code|EUNIS habitat type name|Related habitat type code|to in Annex I to Directive|"
                    r"ELI: http://data\.europa\.eu|OJ L, 29\.7\.2024|^\s*\d+/93\s*$")


def _rows(sources: Path) -> list[dict]:
    pdf = sorted((sources / FOLDER).glob(REGULATION_GLOB))
    if not pdf:
        raise FileNotFoundError(f"{sources / FOLDER}/{REGULATION_GLOB}")
    text = "\n".join(pdftext.pdf_to_lines(pdf[0])).replace("\f", "\n")
    a = text.index("1. Group 1:")
    b = text.index("ANNEX III", a)
    group = region = None
    out: list[dict] = []
    last = None
    for line in text[a:b].split("\n"):
        if not line.strip() or _NOISE.search(line):
            continue
        if line.lstrip().startswith("(1)"):          # footnote of the Annex: skip it and its continuation
            last = None
            continue
        if m := _GROUP.match(line):
            group, region, last = (m.group(1), m.group(2)), None, None
        elif m := _REGION.match(line):
            region, last = m.group(1), None
        elif (m := _ROW.match(line)) and group and region:
            last = {"group": group, "region": region, "code": m.group(1), "name": m.group(2),
                    "annex_i": re.findall(r"\d{4}", m.group(3) or "")}
            out.append(last)
        elif last is not None:                       # wrapped name (may end with Annex I codes)
            m = re.match(r"^\s*(.*?)(?:\s+((?:\d{4};\s*)*\d{4}))?\s*$", line)
            last["name"] += " " + m.group(1).strip()
            last["annex_i"] += re.findall(r"\d{4}", m.group(2) or "")
    for r in out:
        r["name"] = re.sub(r"\s+", " ", r["name"]).strip()
    return out


def habitats(sources: Path) -> pd.DataFrame:
    rows, seen = [], set()
    for r in _rows(sources):
        g, name = r["group"]
        gcode, rcode = f"G{g}", f"G{g}-{REGIONS[r['region']]}"
        if gcode not in seen:
            seen.add(gcode)
            rows.append({"system": "NRL_2024", "code": gcode, "name": name, "level": 1, "parent_code": None,
                         "realm": "marine", "group": None, "description": None, "source": SRC + f", group {g}",
                         "notes": ""})
        if rcode not in seen:
            seen.add(rcode)
            rows.append({"system": "NRL_2024", "code": rcode, "name": f"{name} - {r['region']}", "level": 2,
                         "parent_code": gcode, "realm": "marine", "group": None, "description": None,
                         "source": SRC + f", group {g}, {r['region']}", "notes": ""})
    df = pd.DataFrame(rows)
    df["level"] = df["level"].astype("Int64")
    return df[HABITATS_COLUMNS]


def crosswalks(sources: Path) -> pd.DataFrame:
    rows = []
    for r in _rows(sources):
        g = r["group"][0]
        rows.append({"from_system": "NRL_2024", "from_code": f"G{g}-{REGIONS[r['region']]}",
                     "to_system": "EUNIS_M_2022", "to_code": r["code"], "relationship": ">",
                     "source": SRC + f", group {g}", "notes": f"name in Annex II: {r['name']}"})
        for a in r["annex_i"]:
            rows.append({"from_system": "EUNIS_M_2022", "from_code": r["code"], "to_system": "ANNEX_I", "to_code": a,
                         "relationship": "unspecified",
                         "source": SRC + " (column 'Related habitat type code', from the EEA 2021 crosswalk)",
                         "notes": ""})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()
