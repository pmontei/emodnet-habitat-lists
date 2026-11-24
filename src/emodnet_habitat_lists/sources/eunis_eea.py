"""Crosswalks between EUNIS versions published by the EEA.

Crosswalk produced
------------------
``EUNIS_M_2022 -> EUNIS_2012``: columns "EUNIS 2012 relation(ship)" / "EUNIS 2012 code" of the
three sheets (benthic, pelagic, ice-associated) of the EEA file "EUNIS marine habitat
classification 2022 including crosswalks". Relationships as given (``=``, ``<``, ``>``, ``#``),
read from the EUNIS 2022 unit (``<``: the 2022 unit is narrower than the 2012 unit).

Fixes applied (recorded in ``notes``): a Greek capital alpha typed for "A" (``Α5.4``), non-breaking
spaces, ``A.6`` typed for ``A6`` (``ME2``), one row (``MA223T``) whose 2012 code is in the relationship column and the 2012 name in the
code column, and rows with one relationship for several 2012 codes (applied to all).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ..schema import CROSSWALKS_COLUMNS

SHEETS = {"Benthic habitats": "EUNIS 2012 relation", "Pelagic habitats": "EUNIS 2012 relationship",
          "Ice associated": "EUNIS 2012 relationship"}
SRC = ("EEA 2022, EUNIS marine habitat classification 2022 including crosswalks, sheet '{sheet}', "
       "columns 'EUNIS 2012 relation' / 'EUNIS 2012 code'")
CODE_2012 = re.compile(r"[A-J]\d?(?:\.[0-9A-Z]+)*")
RELS = {"=", "<", ">", "#"}


def _split(v) -> list[str]:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return []
    return [x.strip().replace("\xa0", "") for x in re.split(r";|\n", str(v)) if x.strip().replace("\xa0", "")]


def crosswalk_m2022_2012(eunis_m_2022_xlsx: Path) -> pd.DataFrame:
    rows = []
    for sheet, rel_col in SHEETS.items():
        df = pd.read_excel(eunis_m_2022_xlsx, sheet_name=sheet, dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        for _, r in df[df["EUNIS 2012 code"].notna()].iterrows():
            code22 = str(r["Code"]).strip()
            codes, rels = _split(r["EUNIS 2012 code"]), _split(r[rel_col])
            notes_row = []
            if len(rels) == 1 and CODE_2012.fullmatch(rels[0]) and rels[0] not in RELS and \
                    not any(CODE_2012.fullmatch(c) for c in codes):
                codes, rels = [rels[0]], ["unspecified"]
                notes_row.append("EEA file: 2012 code in the relationship column, name in the code column")
            for i, c in enumerate(codes):
                notes = list(notes_row)
                if "Α" in c:                                     # Greek capital alpha
                    c = c.replace("Α", "A")
                    notes.append("EEA file: Greek letter 'Α' typed for 'A'")
                if re.fullmatch(r"[A-J]\.\d", c):                  # 'A.6' typed for 'A6'
                    notes.append(f"EEA file: '{c}' typed for '{c.replace('.', '')}'")
                    c = c.replace(".", "")
                if not CODE_2012.fullmatch(c):
                    continue
                rel = rels[i] if i < len(rels) else (rels[0] if len(rels) == 1 else "unspecified")
                if len(rels) != len(codes) and not notes_row:
                    notes.append(f"EEA file gives {len(rels)} relationship(s) for {len(codes)} EUNIS 2012 code(s)")
                rows.append({"from_system": "EUNIS_M_2022", "from_code": code22, "to_system": "EUNIS_2012",
                             "to_code": c, "relationship": rel if rel in RELS else "unspecified",
                             "source": SRC.format(sheet=sheet), "notes": "; ".join(notes)})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()
