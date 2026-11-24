"""Crosswalks between EUNIS versions, from the EEA classification files.

Crosswalks produced
-------------------
``EUNIS_M_2022 -> EUNIS_2012``, ``EUNIS_M_2019 -> EUNIS_2012`` and ``EUNIS_T_2021 -> EUNIS_2012``:
columns "EUNIS 2012 relation(ship)" / "EUNIS 2012 code" of the EEA files "EUNIS marine habitat
classification 2022 / 2019 including crosswalks" (sheets benthic, pelagic, ice-associated) and
"EUNIS terrestrial habitat classification 2021_1 including crosswalks" (one sheet per group).
Relationships as given (``=``, ``<``, ``>``, ``#``), read from the revised unit (``<``: the
revised unit is narrower than the 2012 unit). The terrestrial "Man-made" sheet (``V`` codes) is
skipped: its columns are "Code 2018" / "Name 2018" and the ``{eunis.habitats}`` table, from
which EUNIS_T_2021 is loaded, has no ``V`` codes.

``EUNIS_M_2019 -> EUNIS_M_2022``: the EEA publishes no table. The "Read me" sheet of the 2022
file lists the changes (3 new units, ~30 recoded, 2 renamed, 7 moved from the Atlantic to the
Arctic) but not the old -> new codes. The crosswalk is derived by comparing the two files:
units are matched by name first (letters only, case-insensitive), because several codes were
re-used with another meaning (e.g. ``MC1222`` was a *Modiolus* bed in 2019 and is a
*Caryophyllia* community in 2022); a 2022 unit with no name match keeps its 2019 code only if
that 2019 unit was not matched elsewhere (name edited). Every match is ``=``; ``notes`` say
which case applies.

Fixes applied (recorded in ``notes``): a Greek capital alpha typed for "A" (``Α5.4``), non-breaking
spaces, ``A.6`` typed for ``A6`` (``ME2``), one row (``MA223T``) whose 2012 code is in the relationship column and the 2012 name in the
code column, and rows with one relationship for several 2012 codes (applied to all).
"""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from ..schema import CROSSWALKS_COLUMNS

SHEETS = {"Benthic habitats": "EUNIS 2012 relation", "Pelagic habitats": "EUNIS 2012 relationship",
          "Ice associated": "EUNIS 2012 relationship"}
CODE_2012 = re.compile(r"[A-J]\d?(?:\.[0-9A-Z]+)*")
RELS = {"=", "<", ">", "#"}


def _split(v) -> list[str]:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return []
    return [x.strip().replace("\xa0", "") for x in re.split(r"[;,\n]", str(v)) if x.strip().replace("\xa0", "")]


TERRESTRIAL_SHEETS = ["Coastal", "Grassland", "Heathland", "Forest", "Sparsely vegetated", "Wetlands"]
FILES = {
    "EUNIS_M_2022": "EUNIS marine habitat classification 2022 including crosswalks",
    "EUNIS_M_2019": "EUNIS marine habitat classification 2019 including crosswalks",
    "EUNIS_T_2021": "EUNIS terrestrial habitat classification 2021_1 including crosswalks",
}
# the EEA files are also kept, unchanged, in data-raw/ of {eunis.habitats} (CC0); the 2019 and
# terrestrial files are fetched from there (the 2022 file is in the user's source folder too)
DATA_RAW_URL = "https://raw.githubusercontent.com/ramiromagno/eunis.habitats/main/data-raw/"


def fetch_eea_file(system: str, dest_dir: Path, overwrite: bool = False) -> Path:
    """Download the EEA file of ``system`` from ``{eunis.habitats}`` data-raw/ (cached)."""
    dest = Path(dest_dir) / f"{FILES[system]}.xlsx"
    if dest.exists() and not overwrite:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(DATA_RAW_URL + urllib.parse.quote(dest.name), dest)
    return dest


YEAR = {"EUNIS_M_2022": 2022, "EUNIS_M_2019": 2021, "EUNIS_T_2021": 2021}


def crosswalk_m2022_2012(eunis_m_2022_xlsx: Path) -> pd.DataFrame:
    return crosswalk_to_2012(eunis_m_2022_xlsx, "EUNIS_M_2022")


def crosswalk_to_2012(xlsx: Path, system: str) -> pd.DataFrame:
    """``system -> EUNIS_2012`` from the EEA file of ``system`` (see module docstring)."""
    sheets = SHEETS if system != "EUNIS_T_2021" else {s: "EUNIS 2012 relationship" for s in TERRESTRIAL_SHEETS}
    src = (f"EEA {YEAR[system]}, {FILES[system]}, sheet '{{sheet}}', "
           "columns 'EUNIS 2012 relation(ship)' / 'EUNIS 2012 code'")
    rows = []
    for sheet, rel_col in sheets.items():
        df = pd.read_excel(xlsx, sheet_name=sheet, dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        rel_col = rel_col if rel_col in df.columns else "EUNIS 2012 relation"
        for _, r in df[df["EUNIS 2012 code"].notna() & df["Code"].notna()].iterrows():
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
                rows.append({"from_system": system, "from_code": code22, "to_system": "EUNIS_2012",
                             "to_code": c, "relationship": rel if rel in RELS else "unspecified",
                             "source": src.format(sheet=sheet), "notes": "; ".join(notes)})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()


def _units(xlsx: Path) -> pd.DataFrame:
    out = []
    for sheet in SHEETS:
        df = pd.read_excel(xlsx, sheet_name=sheet, dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        df = df[df["Code"].notna()]
        out.append(pd.DataFrame({"code": df["Code"].str.strip(), "name": df["Name"].fillna("").str.strip(),
                                 "sea": df["sea"].fillna("").str.strip(), "sheet": sheet}))
    return pd.concat(out, ignore_index=True)


def _norm(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def crosswalk_m2019_m2022(eunis_m_2019_xlsx: Path, eunis_m_2022_xlsx: Path) -> tuple[pd.DataFrame, list[str]]:
    """``EUNIS_M_2019 -> EUNIS_M_2022`` derived by comparing the two EEA files.

    Returns the crosswalk and the EUNIS 2022 codes with no 2019 equivalent (new units)."""
    u19, u22 = _units(eunis_m_2019_xlsx), _units(eunis_m_2022_xlsx)
    name19 = dict(zip(u19.code, u19.name))
    sea19 = dict(zip(u19.code, u19.sea))
    by_name: dict[str, list[str]] = {}
    for c, n in zip(u19.code, u19.name):
        by_name.setdefault(_norm(n), []).append(c)
    matches: dict[str, tuple[str, str]] = {}            # code 2022 -> (code 2019, case)
    for c, n in zip(u22.code, u22.name):
        m = by_name.get(_norm(n), [])
        if c in m:
            matches[c] = (c, "same")
        elif len(m) == 1:
            matches[c] = (m[0], "recoded")
    used = {v[0] for v in matches.values()}
    new = []
    for c in u22.code:
        if c in matches:
            continue
        if c in name19 and c not in used:
            matches[c] = (c, "renamed")
            used.add(c)
        else:
            new.append(c)
    name22, sea22 = dict(zip(u22.code, u22.name)), dict(zip(u22.code, u22.sea))
    src = ("Derived by comparing the EEA files 'EUNIS marine habitat classification 2019 including "
           "crosswalks' and '... 2022 including crosswalks' (matching by name; see 2022 'Read me' sheet)")
    rows = []
    for c22, (c19, case) in matches.items():
        notes = []
        if case == "recoded":
            notes.append(f"recoded in 2022: same name, 2019 code {c19}")
            if c22 in name19:
                notes.append(f"code {c22} re-used: in EUNIS 2019 it was '{name19[c22]}'")
        elif case == "renamed":
            notes.append(f"same code, name edited in 2022 (2019: '{name19[c19]}')")
        if sea19.get(c19) != sea22.get(c22):
            notes.append(f"regional sea changed {sea19.get(c19)} -> {sea22.get(c22)}")
        rows.append({"from_system": "EUNIS_M_2019", "from_code": c19, "to_system": "EUNIS_M_2022",
                     "to_code": c22, "relationship": "=", "source": src, "notes": "; ".join(notes)})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS), new
