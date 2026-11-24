"""Ramsar Classification System for Wetland Type.

Crosswalk produced
------------------
``RAMSAR -> IUCN_GET`` (``indicative``): the EO4WI "Classification cross-walk" V0.2 (DHI, 2024),
which places each Ramsar wetland type against IUCN Global Ecosystem Typology ecosystem functional
groups (EFG). Each EFG printed in the row of a Ramsar type gives one row. Marine types A, B and C and
the subterranean types Zk(a) and Zk(c) have no EFG in that crosswalk.

The Ramsar list itself (system ``RAMSAR``) is to be loaded from Appendix B of the Strategic
Framework (Resolution XI.8 Annex 2, Rev. COP14) when that file is in the folder; until then the
codes appear in crosswalks only.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import CROSSWALKS_COLUMNS

FOLDER = "15.Ramsar"
CROSSWALK_GLOB = "03_2024_*Crosswalk-Ramsar-IUCN-GET*.pdf"
SRC_DHI = ("DHI et al., 2024. Classification cross-walk V0.2: Ramsar wetland classes crosswalk to IUCN GET and "
           "SDG 6.6.1 - EO4WI (ESA contract 4000141904/23/I-DT)")

MARINE_COASTAL = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "Zk(a)"]
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
