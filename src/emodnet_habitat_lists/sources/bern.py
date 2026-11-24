"""Bern Convention, Resolution No. 4 (1996): habitats requiring specific conservation measures
(Emerald Network), revised Annex I using the EUNIS habitat classification (2019).

System produced
---------------
``EMERALD``
    The habitat types of the revised Annex I to Resolution No. 4 (adopted 6 December 2019), with
    the EUNIS (2012) codes and names under which they are listed, plus the EUNIS group headings
    (``A`` Marine habitats ...) as level-1 rows. The same code values are used by the JNCC
    correlation tables ("Emerald Habitat"). ``description`` comes from the Interpretation Manual
    T-PVS/PA(2019)18 (fourth edition).

Crosswalks produced
-------------------
* ``EMERALD -> EUNIS_2012`` (``=``): each listed type is the EUNIS habitat with that code
  (``X`` habitat complexes are EUNIS 2012 complexes too).
* ``EMERALD -> ANNEX_I``: section "EU Habitats Directive Annex I" of the Interpretation Manual, which
  the manual itself calls indicative. "Same as" ``=``; "Included in" / "Part of" ``<``;
  "Includes" ``>``; "Can occur as part of the following" ``occurs within``; a code without
  qualifier ``unspecified``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS

FOLDER = "13.Bern Convention"
LIST_GLOB = "01_2019_*Resolution-4*.pdf"
MANUAL_GLOB = "02_2019_*Interpretation-manual*.pdf"
SRC = ("Bern Convention Standing Committee, Resolution No. 4 (1996), Revised Annex I on endangered natural habitat "
       "types using the EUNIS habitat classification (adopted 6 December 2019)")
SRC_MANUAL = ("Council of Europe, 2019. Interpretation manual of the habitats listed in Resolution No. 4 (1996), "
              "fourth edition, T-PVS/PA (2019) 18")
ANNEX_CODE = r"[1-9][0-9][0-9A-Z][0-9A-Z]"
_ROW = re.compile(r"^([A-HX](?:\d{1,2}(?:\.[0-9A-Z]+)*)?)\s+(\S.*)$")
_SECTIONS = ("Description", "Plant communities", "Species", "EU Habitats Directive Annex I", "Associated Habitat types",
             "Corresponding", "References", "Subtypes", "Situation")
REALMS = {"A": "marine", "B": "coastal", "X": "complex"}


def _one(pattern: str, sources: Path) -> Path:
    files = sorted((sources / FOLDER).glob(pattern))
    if not files:
        raise FileNotFoundError(f"{sources / FOLDER}/{pattern}")
    return files[0]


def _list(sources: Path) -> list[dict]:
    lines = "\n".join(pdftext.pdf_to_lines(_one(LIST_GLOB, sources))).replace("\f", "\n").split("\n")
    a = next(i for i, l in enumerate(lines) if re.match(r"^A\s+Marine habitats", l.strip()))
    out: list[dict] = []
    pending, attach = None, False
    code_only = re.compile(r"[A-HX]\d{0,2}(?:\.[0-9A-Z]+)*")
    for line in lines[a:]:
        s = line.strip()
        if not s or re.match(r"^-?\s*\d+\s*-?$|^T-PVS", s):
            continue
        if code_only.fullmatch(s):                     # code printed alone, name wrapped around it
            out.append({"code": s, "name": pending or ""})
            pending, attach = None, True
        elif m := _ROW.match(s):
            out.append({"code": m.group(1), "name": ((pending + " ") if pending else "") + m.group(2)})
            pending, attach = None, False
        elif attach or not line.startswith("     "):
            out[-1]["name"] += " " + s
        else:
            pending = (pending + " " + s) if pending else s
    for r in out:
        r["name"] = re.sub(r"\s+", " ", r["name"]).strip()
    return out


def _manual_blocks(sources: Path, codes: set[str]) -> dict[str, list[str]]:
    lines = "\n".join(pdftext.pdf_to_lines(_one(MANUAL_GLOB, sources))).replace("\f", "\n").split("\n")
    lines = [l for l in lines if not re.search(r"T-PVS/PA \(2019\) ?18|^\s*-\s*\d+\s*-\s*$", l)]
    start = [i for i, l in enumerate(lines) if l.strip() == "A MARINE HABITATS"][-1]
    heads = []
    for i in range(start, len(lines)):
        m = re.match(r"^\s{0,8}([A-HX](?:\d{1,2}(?:\.[0-9A-Z]+)*)?)\s+(?:-\s+)?[A-Z(\"']", lines[i])
        if m:
            heads.append((i, m.group(1)))
    blocks: dict[str, list[str]] = {}
    for k, (i, code) in enumerate(heads):
        j = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        if code in codes and code not in blocks and any(l.strip().startswith("Description") for l in lines[i + 1:j]):
            blocks[code] = lines[i + 1:j]
    return blocks


def _section(block: list[str], name: str) -> list[str]:
    out, on = [], False
    for l in block:
        s = l.strip()
        if s.startswith(_SECTIONS) and not (on and s.startswith("Situation")):
            on = s.startswith(name)
            continue
        if on and s:
            out.append(s)
    return out


def habitats(sources: Path) -> pd.DataFrame:
    items = _list(sources)
    blocks = _manual_blocks(sources, {r["code"] for r in items})
    rows = []
    for r in items:
        level = 1 if len(r["code"]) == 1 else 2
        desc = " ".join(_section(blocks.get(r["code"], []), "Description")) or None
        notes = [] if level == 1 else ["EUNIS 2012 code and name"]
        if level == 2 and r["code"] not in blocks:
            notes.append("not found in the Interpretation Manual")
        rows.append({"system": "EMERALD", "code": r["code"], "name": r["name"], "level": level,
                     "parent_code": None if level == 1 else r["code"][0],
                     "realm": REALMS.get(r["code"][0], "terrestrial" if r["code"][0] != "C" else "freshwater"),
                     "group": None, "description": desc,
                     "source": SRC + ("; description: " + SRC_MANUAL if desc else ""),
                     "notes": "; ".join(notes) if level == 2 else "heading (EUNIS group)"})
    df = pd.DataFrame(rows)
    df["level"] = df["level"].astype("Int64")
    return df[HABITATS_COLUMNS]


def crosswalk_eunis(sources: Path) -> pd.DataFrame:
    rows = [{"from_system": "EMERALD", "from_code": r["code"], "to_system": "EUNIS_2012", "to_code": r["code"],
             "relationship": "=", "source": SRC, "notes": "Resolution No. 4 types are listed as EUNIS classes"}
            for r in _list(sources) if len(r["code"]) > 1]
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


_MODES = [(r"^same as", "="), (r"^(?:included in|part of)", "<"), (r"^includes", ">"),
          (r"^can occur as part of", "occurs within")]


def crosswalk_annex_i(sources: Path, annex_codes: set[str] | None = None) -> pd.DataFrame:
    items = [r for r in _list(sources) if len(r["code"]) > 1]
    blocks = _manual_blocks(sources, {r["code"] for r in items})
    rows = []
    for r in items:
        mode = "unspecified"
        for line in _section(blocks.get(r["code"], []), "EU Habitats Directive Annex I"):
            low = line.lower()
            for rx, rel in _MODES:
                if re.match(rx, low):
                    mode = rel
            if "not present in" in low:
                continue
            for c in re.findall(rf"(?<![\d.])({ANNEX_CODE})(?![\d.])", line):
                if annex_codes is not None and c not in annex_codes:
                    continue
                rows.append({"from_system": "EMERALD", "from_code": r["code"], "to_system": "ANNEX_I", "to_code": c,
                             "relationship": mode, "source": SRC_MANUAL + ", section 'EU Habitats Directive Annex I'",
                             "notes": "indicative (manual)"})
            if re.search(ANNEX_CODE, line) and mode in ("=", "<"):
                pass
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates(["from_code", "to_code"])
