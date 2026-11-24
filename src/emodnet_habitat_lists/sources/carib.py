"""Benthic habitat typology of Martinique (Andres et al., 2022) - the classification used by
EUSeaMap for the Caribbean.

System produced
---------------
``CARIB_MARTINIQUE_2022``
    The hierarchical tree of section 2 ("Arbre hiérarchique de la typologie"), five levels:
    1 = zone ("étage", ``A`` supralittoral ... ``F`` abyssal), 2 = substrate (``C2`` substrats durs
    biogènes infralittoraux), 3 = geomorphology (``C2-5`` platiers de récif frangeant ...),
    4 = assemblage (``C2-51``), 5 = habitat (``C2-51.1``). Names are in French, as published.
    ``parent_code`` follows the tree as printed; where the code suggests another parent this is
    flagged in ``notes``.

Crosswalk produced
------------------
``CARIB_MARTINIQUE_2022 -> FR_APHN_ANTILLES`` (``unspecified``): Annex 2, correspondence with the
habitats eligible for the French prefectoral orders for the protection of natural habitats (APHN,
order of 5 August 2019), which use the typology of the French Antilles (Hoff, 1997). ``X`` in the
Annex (no corresponding APHN habitat) gives no row.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS

FOLDER = "12.Caribbean"
TYPOLOGY_GLOB = "*Andres*.pdf"
SRC = ("Andres, S., Ferry, R., Gaudillat, V. & Dirberg, G., 2022. Typologie des habitats benthiques de la "
       "Martinique. PatriNat (OFB-CNRS-MNHN), Paris, 207 p.")
SRC_APHN = SRC + ", Annex 2 (correspondence with the habitats eligible for APHN, order of 5 August 2019)"

_ZONE = re.compile(r"^\s*([A-F])\s+([A-ZÉÈ][A-ZÉÈ ]+?)\s*\.{5,}")
_SUBSTRATE = re.compile(r"^\s*([A-F][1-4])\s+(\S.*)$")
_GEOMORPH = re.compile(r"^\s*([A-F][1-4]-\d{1,2}b?)\s+(\S.*)$")
_ASSEMBLAGE = re.compile(r"^\s*([A-F][1-4]-\d{2,3})\s+(\S.*)$")
_HABITAT = re.compile(r"^\s*([A-F][1-4]-\d{2,3}\.\d)\s+(\S.*)$")
_NOISE = re.compile(r"^\s*\d+\.?\s*$|Typologie des habitats benthiques de la Martinique")


def _pdf(sources: Path) -> Path:
    files = sorted((sources / FOLDER).glob(TYPOLOGY_GLOB))
    if not files:
        raise FileNotFoundError(f"{sources / FOLDER}/{TYPOLOGY_GLOB}")
    return files[0]


def _lines(sources: Path) -> list[str]:
    text = "\n".join(pdftext.pdf_to_lines(_pdf(sources))).replace("\f", "\n")
    return re.sub(r"[\x00-\x08\x0b-\x1f]", "", text).split("\n")


def _tree(lines: list[str]) -> list[dict]:
    starts = [i for i, l in enumerate(lines) if "HIÉRARCHIQUE DE" in l]
    a = starts[-1]
    b = next(i for i in range(a, len(lines)) if "TRANSECTS PÉDAGOGIQUES" in lines[i])
    out: list[dict] = []
    stack: dict[int, str] = {}
    last = None
    for line in lines[a + 1:b]:
        if not line.strip() or _NOISE.search(line):
            continue
        m, level = None, None
        if (m := _ZONE.match(line)):
            level = 1
        elif (m := _HABITAT.match(line)):
            level = 5
        elif (m := _GEOMORPH.match(line) or _ASSEMBLAGE.match(line)):
            name = m.group(2)
            level = 3 if name == name.upper() else 4      # geomorphology headings are in capitals
        elif (m := _SUBSTRATE.match(line)):
            level = 2
        if m:
            code, name = m.group(1), m.group(2).strip()
            if level == 1:
                name = name.capitalize()
            elif level in (2, 3):
                name = name[0] + name[1:].lower()
            last = {"code": code, "name": name, "level": level, "parent": stack.get(level - 1)}
            stack[level] = code
            for k in range(level + 1, 6):
                stack.pop(k, None)
            out.append(last)
        elif last is not None:
            last["name"] += " " + line.strip()
    for r in out:
        r["name"] = re.sub(r"\s+", " ", r["name"]).strip()
    return out


def _expected_parent(code: str, level: int) -> str | None:
    if level == 5:
        return code.split(".")[0]
    if level == 2:
        return code[0]
    if level == 3:
        return code.split("-")[0]
    if level == 4:
        head, num = code.split("-")
        return f"{head}-{num[:-1]}"
    return None


def habitats(sources: Path) -> pd.DataFrame:
    rows = []
    for r in _tree(_lines(sources)):
        notes = []
        exp = _expected_parent(r["code"], r["level"])
        if exp and r["parent"] and exp != r["parent"] and not (exp + "b" == r["parent"]):
            notes.append(f"listed under {r['parent']} in the hierarchical tree; code suggests parent {exp}")
        if r["code"].endswith("b"):
            notes.append("code printed with 'b' in the tree (C2-11 is also an assemblage code)")
        rows.append({"system": "CARIB_MARTINIQUE_2022", "code": r["code"], "name": r["name"], "level": r["level"],
                     "parent_code": r["parent"], "realm": "marine", "group": "benthic", "description": None,
                     "source": SRC + ", section 2 (hierarchical tree)", "notes": "; ".join(notes)})
    df = pd.DataFrame(rows)
    df["level"] = df["level"].astype("Int64")
    return df[HABITATS_COLUMNS]


_ANNEX_ROW = re.compile(r"^\s*([A-F][1-4][-.]\d{2,3}\.\d)\s+\S")
_APHN = re.compile(r"\bA1([12])\.?\s?([0-9A-D])(?=[\s.\-]|$)")


def crosswalk_aphn(sources: Path) -> pd.DataFrame:
    lines = _lines(sources)
    a = next(i for i, l in enumerate(lines) if "HABITATS BENTHIQUES DE LA MARTINIQUE" in l)
    b = next((i for i in range(a, len(lines)) if "ANNEXE 3" in lines[i] or "BANCS DE SARGASSES" in lines[i].upper()
              and i > a + 50), len(lines))
    recs: list[list] = []
    for line in lines[a:b]:
        if m := _ANNEX_ROW.match(line):
            recs.append([m.group(1), [], line])
        if recs:
            for g in _APHN.finditer(line):
                recs[-1][1].append(f"A1{g.group(1)}.{g.group(2)}")
    tree = {r["code"]: r["name"] for r in _tree(lines) if r["level"] == 5}
    by_name = {_norm(n): c for c, n in tree.items()}
    rows = []
    for code, aphn, first in recs:
        notes = []
        printed = code
        code = re.sub(r"^([A-F][1-4])\.", r"\1-", code)
        if code not in tree:
            name = re.sub(r"\s{2,}.*$", "", first.strip()[len(printed):].strip())
            match = next((c for k, c in by_name.items() if k.startswith(_norm(name)[:25])), None)
            if match:
                code = match
        if code != printed:
            notes.append(f"printed as '{printed}' in Annex 2")
        for x in dict.fromkeys(aphn):
            rows.append({"from_system": "CARIB_MARTINIQUE_2022", "from_code": code, "to_system": "FR_APHN_ANTILLES",
                         "to_code": x, "relationship": "unspecified", "source": SRC_APHN, "notes": "; ".join(notes)})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
