"""Habitats Directive (92/43/EEC) Annex I natural habitat types.

System produced
---------------
``ANNEX_I``
    The 233 Annex I habitat types of the consolidated Directive (01/07/2013, after the accession
    of Croatia), with their headings: level 1 = habitat group (``1`` ... ``9``), level 2 =
    sub-group (``11``, ``12`` ...), level 3 = habitat type (``1110`` ...). Priority habitat types
    (``*`` in the Directive) are flagged in ``notes``; the ``*`` is not part of the name.
    ``description`` is section 1) (definition) of the Interpretation Manual EUR28 (April 2013).

Crosswalks produced
-------------------
* ``ANNEX_I -> EUNIS_2012`` (``partim``): the "EUNIS classification: Relevant types within ..."
  statements in section 3) of the Interpretation Manual (only 1110, 1170 and 1180 have one).
* ``ANNEX_I -> PAL_CLASS`` (``unspecified``): the ``PAL.CLASS.`` line of each manual entry
  (Palaearctic habitat classification, Devillers & Devillers-Terschuren 1996).
* ``EUNIS_M_2022 -> ANNEX_I``: columns "Annex I relationship" / "Annex I code" of the EEA file
  "EUNIS marine habitat classification 2022 including crosswalks" (benthic sheet).

``realm`` is assigned by this repository (not by the sources): ``marine`` for the types of the
Commission's marine guidelines (sub-group 11, 1610, 1620, 1650 and 8330), ``coastal`` for the
rest of groups 1 and 2, ``freshwater`` for group 3 and ``terrestrial`` for groups 4 to 9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS

FOLDER = "6.EU Habitats Directive"
DIRECTIVE_GLOB = "01_2013_*consolidated*.pdf"
MANUAL_GLOB = "03_2013_*Interpretation-Manual*EUR28*.pdf"

SRC_DIRECTIVE = ("Council Directive 92/43/EEC, consolidated version 01/07/2013 (CELEX 01992L0043-20130701), "
                 "Annex I")
SRC_MANUAL = "European Commission DG ENV, 2013. Interpretation Manual of European Union Habitats - EUR28 (April 2013)"
SRC_EEA = ("EEA 2022, EUNIS marine habitat classification 2022 including crosswalks, sheet 'Benthic habitats', "
           "columns 'Annex I relationship' / 'Annex I code'")

CODE = r"[1-9][0-9][0-9A-Z]{2}"
MARINE = {"1610", "1620", "1650", "8330"}
EUNIS_2012_CODE = r"[A-J][0-9](?:\.[0-9A-Z]+)*"


def _one(folder: Path, pattern: str) -> Path:
    files = sorted(folder.glob(pattern))
    if not files:
        raise FileNotFoundError(f"{folder}/{pattern}")
    return files[0]


def _clean(s: str) -> str:
    s = s.replace("­ ", "").replace("­", "")       # soft hyphen at line breaks
    return re.sub(r"\s+", " ", s).strip()


def _realm(code: str) -> str:
    if code.startswith("11") or code in MARINE:
        return "marine"
    return {"1": "coastal", "2": "coastal", "3": "freshwater"}.get(code[0], "terrestrial")


def _directive_entries(pdf: Path) -> list[dict]:
    text = "\n".join(pdftext.pdf_to_lines(pdf))
    a = text.index("1. COASTAL AND HALOPHYTIC HABITATS")
    b = text.index("ANNEX II", a)
    lines = text[a:b].replace("\f", "\n").split("\n")
    group = re.compile(r"^\s*([1-9])\.\s+([A-Z][A-Z ,()\-—'’]+)$")
    sub = re.compile(r"^\s*([1-9][0-9])\.\s+(\S.*)$")
    hab = re.compile(rf"^\s*({CODE})\s+(\*\s*)?(\S.*)$")
    entries: list[dict] = []
    last = None
    for line in lines:
        if not line.strip() or line.lstrip().startswith(("▼", "(+)", "01992L0043")):
            last = None
            continue
        m = group.match(line) or sub.match(line) or hab.match(line)
        if m and m.re is group:
            last = {"code": m.group(1), "name": m.group(2).strip().capitalize(), "level": 1,
                    "parent": None, "priority": False}
        elif m and m.re is sub:
            last = {"code": m.group(1), "name": m.group(2), "level": 2, "parent": m.group(1)[0],
                    "priority": False}
        elif m:
            last = {"code": m.group(1), "name": m.group(3), "level": 3, "parent": m.group(1)[:2],
                    "priority": bool(m.group(2))}
            if not any(x["code"] == last["parent"] for x in entries):   # group 4 has no sub-groups
                last["parent"] = last["code"][0]
        elif last is not None and last["level"] > 1:   # continuation of a wrapped name
            sep = "" if last["name"].endswith("-") and not last["name"].endswith(" -") else " "
            last["name"] += sep + line.strip()
            continue
        elif last is not None:              # text under a group heading (group 9 criteria)
            last["description"] = (last.get("description", "") + " " + line.strip()).strip()
            continue
        else:
            continue
        entries.append(last)
    for e in entries:
        e["name"] = _clean(e["name"])
    return entries


def _manual_entries(pdf: Path, codes: set[str]) -> dict[str, dict]:
    """Return {code: {"definition", "pal", "eunis"}} from the Interpretation Manual."""
    lines = pdftext.pdf_to_lines(pdf)
    lines = [l for l in "\n".join(lines).replace("\f", "\n").split("\n")
             if not re.match(r"^\s*Interpretation Manual - EUR28\s+Page \d+\s*$", l)]
    head = re.compile(rf"^\s{{0,3}}({CODE})\b\s*\S")
    starts = []
    for i, l in enumerate(lines):
        m = head.match(l)
        if m and m.group(1) in codes and any("PAL.CLASS" in x for x in lines[i:i + 7]):
            starts.append((i, m.group(1)))
    out = {}
    for k, (i, code) in enumerate(starts):
        block = lines[i:starts[k + 1][0] if k + 1 < len(starts) else len(lines)]
        txt = "\n".join(block)
        pal = re.search(r"PAL\.CLASS\.?\s*:?[ \t]*(.*)", txt)
        # section markers '1)', '2)', '3)' (once printed '3' without parenthesis), after the heading line
        sec = {}
        for n in ("1", "2", "3", "4"):
            pat = rf"(?m)^\s*{n}\)\s+(?=\S)" + (r"|^\s*3\s+Corresponding" if n == "3" else "")
            m = re.compile(pat).search(txt, txt.index("\n") + 1)
            sec[n] = m.start() if m else None
        d0 = sec["1"]
        d1 = next((sec[n] for n in ("2", "3", "4") if sec[n] and d0 is not None and sec[n] > d0), None)
        definition = re.sub(r"^\s*1\)?\s*", "", txt[d0:d1]) if d0 is not None else ""
        eunis = re.search(r"EUNIS(?: classification)?:\s*(Relevant types (?:within|under)\s*“?(.*?)”?\.?)\s*(?:\n\s*\n|\n\s*[A-Z][a-zA-Z ]+classification|\n\s*4\)|$)",
                          txt, re.S)
        out[code] = {
            "definition": _clean(definition),
            "pal": _clean(pal.group(1)) if pal and not re.match(r"\s*1\)", pal.group(1)) else "",
            "eunis": (_clean(eunis.group(1)), re.findall(rf"\b({EUNIS_2012_CODE})\s", _clean(eunis.group(2)) + " "))
            if eunis else None,
        }
    return out


def _paths(sources: Path) -> tuple[Path, Path]:
    folder = sources / FOLDER
    return _one(folder, DIRECTIVE_GLOB), _one(folder, MANUAL_GLOB)


def habitats(sources: Path) -> pd.DataFrame:
    directive, manual = _paths(sources)
    entries = _directive_entries(directive)
    man = _manual_entries(manual, {e["code"] for e in entries if e["level"] == 3})
    rows = []
    for e in entries:
        notes = []
        if e["priority"]:
            notes.append("priority habitat type (*)")
        m = man.get(e["code"]) if e["level"] == 3 else None
        if e["level"] == 3 and m is None:
            notes.append("not found in the Interpretation Manual EUR28")
        rows.append({
            "system": "ANNEX_I", "code": e["code"], "name": e["name"], "level": e["level"],
            "parent_code": e["parent"], "realm": _realm(e["code"]) if e["level"] == 3 else None,
            "group": None, "description": (m or {}).get("definition") or e.get("description") or None,
            "source": SRC_DIRECTIVE + ("; description: " + SRC_MANUAL + ", section 1)" if m else ""),
            "notes": "; ".join(notes),
        })
    df = pd.DataFrame(rows)
    df["level"] = df["level"].astype("Int64")
    return df[HABITATS_COLUMNS]


def _pal_items(expr: str) -> list[tuple[str, str, str]]:
    """Split a PAL.CLASS. line into (code, relationship, note).

    Simple items ('11.24', '18.23 and 18.24', '22.12p', '42C51 (1997 version)') give one row per
    code; a trailing 'p' / '(p)' (pro parte) gives ``partim``. Compound expressions
    ('22.11 x 22.31', '16.221 to 16.227', '(64.11 or 64.12) x 35.2') are kept as printed.
    """
    out = []
    for item in (x.strip() for x in expr.split(",")):
        if not item or item == "-":
            continue
        note = []
        if "(1997 version)" in item:
            item = item.replace("(1997 version)", "").strip()
            note.append("Palaearctic classification 1997 version")
        item = re.sub(r"\s*\(p\)$", "p", item)
        if re.search(r" x |\bto\b|\bor\b|=|\(", item):
            out.append((item, "unspecified", "; ".join(note + ["compound expression as printed ('x' = combination)"])))
            continue
        for c in (x.strip() for x in item.split(" and ")):
            rel = "unspecified"
            if c.endswith("p"):
                c, rel = c[:-1], "partim"
            out.append((c, rel, "; ".join(note)))
    return out


def crosswalk_manual(sources: Path) -> pd.DataFrame:
    directive, manual = _paths(sources)
    codes = {e["code"] for e in _directive_entries(directive) if e["level"] == 3}
    rows = []
    for code, m in _manual_entries(manual, codes).items():
        for to_code, rel, note in _pal_items(m["pal"]):
            rows.append({"from_system": "ANNEX_I", "from_code": code, "to_system": "PAL_CLASS", "to_code": to_code,
                         "relationship": rel, "source": SRC_MANUAL + ", PAL.CLASS.", "notes": note})
        if m["eunis"]:
            statement, eunis_codes = m["eunis"]
            for c in eunis_codes:
                rows.append({"from_system": "ANNEX_I", "from_code": code, "to_system": "EUNIS_2012", "to_code": c,
                             "relationship": "partim", "source": SRC_MANUAL + ", section 3) Corresponding categories",
                             "notes": f"manual: '{statement[:60]}...' (EUNIS version 2.3, 2002)"})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


def _split(v) -> list[str]:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return []
    v = str(v).replace("_x000D_", "")
    return [x.strip() for x in re.split(r"[;\n]+", v) if x.strip()]


def crosswalk_eunis2022(eunis_m_2022_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(eunis_m_2022_xlsx, sheet_name="Benthic habitats", dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    rows = []
    for _, r in df.iterrows():
        codes = [c for c in _split(r.get("Annex I code")) if re.fullmatch(CODE, c)]
        rels = _split(r.get("Annex I relationship"))
        for i, c in enumerate(codes):
            rel = rels[i] if i < len(rels) else (rels[-1] if len(rels) == 1 else "unspecified")
            note = "" if len(rels) == len(codes) else (
                f"EEA file gives {len(rels)} relationship(s) for {len(codes)} Annex I code(s)")
            rows.append({"from_system": "EUNIS_M_2022", "from_code": str(r["Code"]).strip(), "to_system": "ANNEX_I",
                         "to_code": c, "relationship": rel, "source": SRC_EEA, "notes": note})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()
