"""Ramsar Classification System for Wetland Type.

Crosswalk produced
------------------
``RAMSAR -> IUCN_GET`` (``indicative``): the EO4WI "Classification cross-walk" V0.2 (DHI, 2024),
which places each Ramsar wetland type against IUCN Global Ecosystem Typology ecosystem functional
groups (EFG). Each EFG printed in the row of a Ramsar type gives one row. Marine types A, B and C and
the subterranean types Zk(a) and Zk(c) have no EFG in that crosswalk.

System produced
---------------
``RAMSAR``
    The wetland types of Appendix B of the Strategic Framework (COP11 Resolution XI.8 Annex 2,
    Rev. COP14): 13 marine/coastal (including ``Ga`` Bivalve (shellfish) reefs, added after the
    EO4WI crosswalk's source list), 20 inland and 10 human-made types. Level 1 = the three groups
    (``MC``, ``IN``, ``HM``), level 2 = wetland type. ``name`` is the text before the first ';',
    the rest of the definition goes to ``description``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS

FOLDER = "15.Ramsar"
CROSSWALK_GLOB = "03_2024_*Crosswalk-Ramsar-IUCN-GET*.pdf"
FRAMEWORK_GLOB = "01_*Resolution-XI8*.pdf"
SRC = ("Ramsar Convention, COP11 Resolution XI.8 Annex 2 (Rev. COP14): Strategic Framework and guidelines for the "
       "future development of the List of Wetlands of International Importance, Appendix B: Ramsar Classification "
       "System for Wetland Type")
SRC_DHI = ("DHI et al., 2024. Classification cross-walk V0.2: Ramsar wetland classes crosswalk to IUCN GET and "
           "SDG 6.6.1 - EO4WI (ESA contract 4000141904/23/I-DT)")

MARINE_COASTAL = ["A", "B", "C", "D", "E", "F", "G", "Ga", "H", "I", "J", "K", "Zk(a)"]
INLAND = ["L", "M", "N", "O", "P", "Q", "R", "Sp", "Ss", "Tp", "Ts", "U", "Va", "Vt", "W", "Xf", "Xp", "Y", "Zg",
          "Zk(b)"]
HUMAN_MADE = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "Zk(c)"]

_TYPE = re.compile(r"(?:(?<=\s)|^)(Zk\([abc]\)|Zg|Vt|Va|Tp|Ts|Sp|Ss|Xf|Xp|[A-Y])(?=,)")
_HUMAN = re.compile(r"^\s*([1-9]) --")
_EFG = re.compile(r"\b(MFT1\.\d|FM1\.\d|MT1\.\d|TF1\.\d|T\d\.\d|F\d\.\d{1,2}|M\d\.\d)\b")


def crosswalk_get(sources: Path) -> pd.DataFrame:
    files = sorted((sources / FOLDER).glob(CROSSWALK_GLOB))
    if not files:
        raise FileNotFoundError(f"{sources / FOLDER}/{CROSSWALK_GLOB}")
    lines = "\n".join(pdftext.pdf_to_lines(files[0])).replace("\f", "\n").split("\n")
    end = next(i for i, l in enumerate(lines) if "IUCN GET based feasibility" in l)
    cur, out = None, {}
    for line in lines[:end]:
        m = (_TYPE.search(line) or _HUMAN.match(line) or re.search(r"\b(Zk\([ac]\))", line)
             or re.search(r"(?<=\s)(M)(?= Permanent)", line))
        if m:
            cur = m.group(1)
            out.setdefault(cur, [])
        if cur:
            for e in _EFG.findall(line):
                if e not in out[cur]:
                    out[cur].append(e)
    rows = [{"from_system": "RAMSAR", "from_code": t, "to_system": "IUCN_GET", "to_code": e,
             "relationship": "indicative", "source": SRC_DHI, "notes": "project crosswalk draft (V0.2)"}
            for t, efgs in out.items() for e in efgs]
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


GROUPS = {"Marine/Coastal Wetlands": ("MC", "Marine/coastal wetlands", "marine"),
          "Inland Wetlands": ("IN", "Inland wetlands", "freshwater"),
          "Human-made wetlands": ("HM", "Human-made wetlands", "artificial")}
_ROW = re.compile(r"^\s*(Zk\([abc]\)|[A-Z][a-z]?|[1-9])\s+(?:--|–)\s+(\S.*)$")


def habitats(sources: Path) -> pd.DataFrame:
    files = sorted((sources / FOLDER).glob(FRAMEWORK_GLOB))
    if not files:
        raise FileNotFoundError(f"{sources / FOLDER}/{FRAMEWORK_GLOB}")
    lines = "\n".join(pdftext.pdf_to_lines(files[0])).replace("\f", "\n").split("\n")
    a = next(i for i, l in enumerate(lines) if l.strip() == "Ramsar Classification System for Wetland Type"
             and i > 1000)
    b = next(i for i in range(a, len(lines)) if "Tabulations of Wetland Type characteristics" in lines[i])
    rows, group, last = [], None, None
    for line in lines[a:b]:
        s = line.strip()
        if s in GROUPS:
            group = GROUPS[s]
            rows.append({"code": group[0], "text": group[1], "level": 1, "parent": None, "realm": group[2]})
            last = None
            continue
        if group is None or not s or s.startswith(("Ramsar COP11", "Note:")) or "floodplain" in s.lower() and last is None:
            last = None if s.startswith("Note:") else last
            continue
        if m := _ROW.match(line):
            last = {"code": m.group(1), "text": m.group(2), "level": 2, "parent": group[0], "realm": group[2]}
            rows.append(last)
        elif last is not None and line.startswith(" "):
            last["text"] += " " + s
    out = []
    for r in rows:
        text = re.sub(r"\s+", " ", r["text"]).strip().rstrip(".")
        name, _, rest = text.partition(";")
        out.append({"system": "RAMSAR", "code": r["code"], "name": name.strip(), "level": r["level"],
                    "parent_code": r["parent"], "realm": r["realm"], "group": None,
                    "description": text + "." if r["level"] == 2 and rest else None,
                    "source": SRC, "notes": "group code assigned by this repository" if r["level"] == 1 else ""})
    df = pd.DataFrame(out)
    df["level"] = df["level"].astype("Int64")
    return df[HABITATS_COLUMNS]
