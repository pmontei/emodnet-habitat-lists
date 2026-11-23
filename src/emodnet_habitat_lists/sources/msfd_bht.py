"""MSFD benthic broad habitat types (Commission Decision (EU) 2017/848, Annex, Part II, Table 2).

System produced
---------------
``MSFD_BHT``
    The benthic broad habitat types of Table 2. The Decision gives no codes: ``code`` is a slug of
    the name (``infralittoral-sand``), as for OSPAR. Footnote (2) on the upper/lower bathyal
    boundary is kept in ``notes``.

Crosswalk produced
------------------
``MSFD_BHT -> EUNIS_M_2022``: the "Relevant EUNIS habitat codes (version 2016)" column. The
Decision says each broad habitat type "equate[s] to one or more" EUNIS habitat types, so the
relationship is ``=`` when one EUNIS code is listed and ``>`` (the broad habitat type contains
the EUNIS habitat) when several are listed. The 2016 level-2 codes are unchanged in the EUNIS
marine 2019 and 2022 classifications; names may differ (e.g. ``MB2``).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS

FOLDER = "7.MSFD broad habitat types"
DECISION_GLOB = "01_2017_*2017-848*.pdf"
SRC = ("Commission Decision (EU) 2017/848 of 17 May 2017 (OJ L 125, 18.5.2017, p. 43), Annex, Part II, "
       "Theme 'Benthic habitats', Table 2")
FOOTNOTE_2 = ("Decision 2017/848, Table 2, footnote (2): where not specifically defined in the EUNIS "
              "classification, the boundary between the upper and lower bathyal may be set as a specified depth limit")
EUNIS_L2 = r"M[A-G][1-6]"


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _table(sources: Path) -> list[tuple[str, list[str], bool]]:
    pdf = sorted((sources / FOLDER).glob(DECISION_GLOB))
    if not pdf:
        raise FileNotFoundError(f"{sources / FOLDER}/{DECISION_GLOB}")
    text = "\n".join(pdftext.pdf_to_lines(pdf[0]))
    a = text.index("Benthic broad habitat types including their associated biological communities")
    b = text.index("(1) Evans, D. (2016)", a)
    row = re.compile(rf"^\s*(?:Benthic habitats\s+)?(\S.*?\S)\s{{3,}}({EUNIS_L2}(?:,\s*{EUNIS_L2})*,?)\s*$")
    more = re.compile(rf"^\s*({EUNIS_L2}(?:,\s*{EUNIS_L2})*)\s*$")
    out: list[tuple[str, list[str], bool]] = []
    for line in text[a:b].split("\n"):
        if m := row.match(line):
            name = m.group(1)
            fn = "(2)" in name
            name = re.sub(r"\s*\(2\)\s*", " ", name).strip()
            out.append((name, re.findall(EUNIS_L2, m.group(2)), fn))
        elif (m := more.match(line)) and out:        # wrapped code list ('MG6')
            out[-1][1].extend(re.findall(EUNIS_L2, m.group(1)))
    return out


def habitats(sources: Path) -> pd.DataFrame:
    rows = [{
        "system": "MSFD_BHT", "code": slug(n), "name": n, "level": 1, "parent_code": None,
        "realm": "marine", "group": "benthic", "description": None, "source": SRC,
        "notes": "code is a slug of the name (no official codes)" + ("; " + FOOTNOTE_2 if fn else ""),
    } for n, _, fn in _table(sources)]
    df = pd.DataFrame(rows)
    df["level"] = df["level"].astype("Int64")
    return df[HABITATS_COLUMNS]


def crosswalk_eunis(sources: Path) -> pd.DataFrame:
    rows = []
    for n, codes, _ in _table(sources):
        for c in codes:
            rows.append({"from_system": "MSFD_BHT", "from_code": slug(n), "to_system": "EUNIS_M_2022", "to_code": c,
                         "relationship": "=" if len(codes) == 1 else ">",
                         "source": SRC + ", column 'Relevant EUNIS habitat codes (version 2016)'",
                         "notes": "EUNIS version 2016 in the Decision; level-2 codes unchanged in EUNIS marine 2022"})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)
