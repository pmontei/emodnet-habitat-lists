"""IUCN Global Ecosystem Typology (GET) 2.0.

System produced
---------------
``IUCN_GET``
    Levels 1-3 of the typology: realms (level 1, ``T``, ``M``, ``MT`` ...), biomes (level 2, ``M1``)
    and ecosystem functional groups (EFG, level 3, ``M1.1``), from the contents of Keith et al.
    (2020), "The IUCN Global Ecosystem Typology 2.0: Descriptive profiles", Part II. Realm names are
    those printed in the EFG profiles ("REALM: TRANSITIONAL FRESHWATER-MARINE" ...); the Atmospheric
    realm has no EFGs in 2.0 and is not listed. ``realm`` gives the repository's realm label
    (``marine`` for M, MT, MFT, FM and SM).

Version 2.1 (2022) is maintained online (https://global-ecosystems.org). Its EFGs used by other
sources of this repository but absent from 2.0 are added from those sources (``V21_ADDITIONS``):
``M1.10`` "Rhodolith/Maerl beds" (JNCC correlation tables 2026).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import HABITATS_COLUMNS

FOLDER = "17.IUCN Global Ecosystem Typology"
GET_GLOB = "01_2020_*Global-Ecosystem-Typology*.pdf"
SRC = ("Keith, D.A., Ferrer-Paris, J.R., Nicholson, E. and Kingsford, R.T. (eds.) (2020). The IUCN Global Ecosystem "
       "Typology 2.0: Descriptive profiles for biomes and ecosystem functional groups. IUCN, "
       "doi:10.2305/IUCN.CH.2020.13.en")
REALMS = {
    "T": "Terrestrial", "S": "Subterranean", "F": "Freshwater", "M": "Marine",
    "TF": "Freshwater-Terrestrial", "SF": "Subterranean-Freshwater", "SM": "Subterranean-Marine",
    "FM": "Freshwater-Marine", "MT": "Marine-Terrestrial", "MFT": "Terrestrial-Freshwater-Marine",
}
REPO_REALM = {"T": "terrestrial", "S": "subterranean", "F": "freshwater", "TF": "freshwater", "SF": "subterranean",
              "M": "marine", "SM": "marine", "FM": "marine", "MT": "marine", "MFT": "marine"}
V21_ADDITIONS = [("M1.10", "Rhodolith/Maerl beds", "JNCC marine habitat correlation tables v2026.02 (GET v2.1)")]
_BIOME = re.compile(r"^\s*((?:MFT|MT|FM|SF|SM|TF|M|F|T|S)\d)\s+(\S.*?biome)\s+\d+\s*$")
_EFG = re.compile(r"^\s*((?:MFT|MT|FM|SF|SM|TF|M|F|T|S)\d\.\d{1,2})\s+(\S.*?)\s+\d+\s*$")


def _contents(sources: Path) -> list[tuple[int, str, str]]:
    files = sorted((sources / FOLDER).glob(GET_GLOB))
    if not files:
        raise FileNotFoundError(f"{sources / FOLDER}/{GET_GLOB}")
    lines = "\n".join(pdftext.pdf_to_lines(files[0])).replace("\f", "\n").split("\n")
    a = next(i for i, l in enumerate(lines) if re.match(r"^\s*Part II\s+\d+\s*$", l))
    b = next(i for i in range(a, len(lines)) if lines[i].strip().startswith("List of figures"))
    out = []
    for l in lines[a:b]:
        if m := _EFG.match(l):
            out.append((3, m.group(1), m.group(2)))
        elif m := _BIOME.match(l):
            out.append((2, m.group(1), m.group(2)))
    return out


def habitats(sources: Path) -> pd.DataFrame:
    items = _contents(sources)
    rows = []
    for code, name in REALMS.items():
        rows.append({"system": "IUCN_GET", "code": code, "name": name + " realm", "level": 1, "parent_code": None,
                     "realm": REPO_REALM[code], "group": None, "description": None, "source": SRC + ", Part I",
                     "notes": "core realm" if len(code) == 1 else "transitional realm"})
    for level, code, name in items:
        realm = re.match(r"[A-Z]+", code).group()
        parent = realm if level == 2 else code.split(".")[0]
        rows.append({"system": "IUCN_GET", "code": code, "name": name, "level": level, "parent_code": parent,
                     "realm": REPO_REALM[realm], "group": "biome" if level == 2 else "ecosystem functional group",
                     "description": None, "source": SRC + ", contents of Part II", "notes": ""})
    for code, name, src in V21_ADDITIONS:
        rows.append({"system": "IUCN_GET", "code": code, "name": name, "level": 3, "parent_code": code.split(".")[0],
                     "realm": "marine", "group": "ecosystem functional group", "description": None, "source": src,
                     "notes": "GET v2.1 EFG, not in v2.0"})
    df = pd.DataFrame(rows)
    df["level"] = df["level"].astype("Int64")
    return df[HABITATS_COLUMNS]
