"""Palaearctic Habitat Classification (PHYSIS 2001) and CORINE biotopes (1991).

Systems produced
----------------
``PAL_CLASS``: Devillers, Devillers-Terschuren & Vander Linden (2001), PHYSIS Palaearctic Habitat
Classification, updated to 10 December 2001, as tabulated by SPN-MNHN / INPN (table
TYPO_PAL_PHYSIS_2001, sheet "Données"): 6228 codes with parent, level (1-8), English name and
description. Realm from the first digit (1 coastal and halophytic, 2 non-marine waters, ...).

``CORINE``: CORINE biotopes manual, Volume 3 (CEC 1991), **chapters 1 (coastal and halophytic
communities) and 2 (non-marine waters) only**. The PDF is a scan with an OCR text layer:

* entries are the lines that start with a code followed by a name (contents and index lines,
  which end with a page number, are skipped); a short following line is a wrapped name;
* headings printed in capitals followed by a syntaxon name (e.g. "GLASSWORT SWARDS
  Thero-Salicornietalia") keep the heading as name and the syntaxon in ``notes``;
* OCR spacing inside words is repaired with the vocabulary of the PAL names and descriptions
  (e.g. "Inshore wa ters" -> "Inshore waters"), and "1" between letters is read as "I";
* when the PAL unit with the same code has a near-identical name (similarity >= 0.85), the PAL
  spelling is used (it fixes OCR errors such as "Fuat-leaved" -> "Flat-leaved"); otherwise the
  OCR name is kept and flagged ``OCR text, to check`` when it still looks damaged.
"""

from __future__ import annotations

import difflib
import re
from pathlib import Path

import pandas as pd

from ..pdftext import pdf_to_lines
from ..schema import HABITATS_COLUMNS

PAL_FOLDER = "21.Palaearctic Habitat Classification"
PAL_GLOB = "*PHYSIS*TYPO-PAL*.xls"
SRC_PAL = ("Devillers, P., Devillers-Terschuren, J. & Vander Linden, C., 2001. PHYSIS Palaearctic Habitat "
           "Classification, updated to 10 December 2001 (IRSNB); table TYPO_PAL_PHYSIS_2001, SPN-MNHN / INPN 2010")
CORINE_FOLDER = "20.CORINE Biotopes"
CORINE_GLOB = "*CORINE-Biotopes-Manual*.pdf"
SRC_CORINE = ("Commission of the European Communities, 1991. CORINE biotopes manual. Habitats of the European "
              "Community. Data specifications - Part 2 (Vol. 3), EUR 12587/3 EN, chapters 1-2")
PAL_REALM = {"1": "marine", "2": "freshwater"}
CORINE_CHAPTERS = {"1", "2"}

_CODE = r"(?:\d{1,2}(?:\.\d{1,5})*)"
_LINE = re.compile(rf"^(?:I\s+)?(\s{{0,45}})({_CODE}|ll\.[\dl£]+)\.?\s+(\S.{{0,110}})$")
_CODE_ONLY = re.compile(rf"^(?:I\s+)?\s{{0,45}}({_CODE})\.?\s*$")
_DAMAGED = re.compile(r"[^A-Za-z0-9 ,;:'()\-/.&]|\b[a-z]\b(?<!\ba\b)|\.\w|\b[A-Z][a-z]*[A-Z]|\d")


# names damaged by the OCR, read on the page image of the manual: code -> (name, syntaxon or "")
OCR_FIXES = {
    "15": ("Salt marshes, salt steppes and gypsum scrubs", ""),
    "15.31": ("Saltmarsh grass meadows", ""),
    "15.1122": ("Continental drier glasswort swards", ""),
    "16.28": ("Dune sclerophyllous scrubs", ""),
    "16.272": ("Lycian juniper woods", ""),
    "15.56": ("Mediterranean saltmarsh driftlines", "Thero-Suaedion"),
    "24.224": ("Gravel bank thickets and woods", ""),
    "18.22": ("Mediterranean cliff communities", "Crithmo-Limonietalia"),
    "22.431": ("Floating broad-leaved carpets", "Nymphaeion albae"),
    "23.211": ("Tasselweed communities", "Ruppion maritimae p."),
}


# entries whose code or whole block is missing from the OCR text layer, read on the page images
MISSING_FROM_OCR = {
    "22.2": "Unvegetated muds or shingles",                   # p. 39 of the manual (heading without code in OCR)
    "24.42": "Lime-rich oligotrophic river vegetation",       # p. 47 (block missing in OCR)
}


def _one(folder: Path, pattern: str) -> Path | None:
    files = sorted(folder.glob(pattern))
    return files[0] if files else None


def pal_table(sources: Path) -> pd.DataFrame:
    f = _one(sources / PAL_FOLDER, PAL_GLOB)
    if f is None:
        raise FileNotFoundError(f"{sources / PAL_FOLDER}: {PAL_GLOB} not found")
    return pd.read_excel(f, sheet_name="Données", dtype=str)


def pal_habitats(sources: Path) -> pd.DataFrame:
    d = pal_table(sources)
    out = pd.DataFrame({
        "system": "PAL_CLASS", "code": d.CD_PAL.str.strip(), "name": d.LB_PAL_EN.str.strip(),
        "level": pd.to_numeric(d.NIVEAU), "parent_code": d.CD_PAL_SUP.str.strip(),
        "realm": d.CD_PAL.str[0].map(PAL_REALM).fillna("terrestrial"),
        "group": d.CD_PAL.str.split(".").str[0].str[:2], "description": d.DESCRIPTIF,
        "source": SRC_PAL, "notes": ""}, columns=HABITATS_COLUMNS)
    out["level"] = out["level"].astype("Int64")
    return out


def _sim(a: str, b: str) -> float:
    n = lambda s: re.sub(r"\W", "", s.lower())
    return difflib.SequenceMatcher(None, n(a), n(b)).ratio()


def corine_habitats(sources: Path) -> pd.DataFrame:
    pdf = _one(sources / CORINE_FOLDER, CORINE_GLOB)
    if pdf is None:
        raise FileNotFoundError(f"{sources / CORINE_FOLDER}: {CORINE_GLOB} not found")
    pal = pal_table(sources)
    pal_name = dict(zip(pal.CD_PAL.str.strip(), pal.LB_PAL_EN.str.strip()))
    vocab = {w.lower() for t in pd.concat([pal.LB_PAL_EN, pal.DESCRIPTIF.fillna("")])
             for w in re.findall(r"[A-Za-z]+", str(t))}

    def repair(name: str) -> str:
        name = re.sub(r"(?<=[A-Za-z])1(?=[A-Za-z])", "I", name)
        out: list[str] = []
        for t in name.split():
            core = t.lower().strip(",;.")
            if out and (out[-1] + t).lower().strip(",;.") in vocab and (out[-1].lower() not in vocab or core not in vocab):
                out[-1] += t
            else:
                out.append(t)
        return " ".join(out)

    lines = pdf_to_lines(pdf)
    entries: dict[str, tuple[str, str]] = {}
    for i, s in enumerate(lines):
        m = _LINE.match(s)
        if m:
            code, name = m.group(2), m.group(3).strip()
        else:
            # code alone on its line: the heading is the next line in capitals (13.11 / BRACKISH WATER), or a
            # short title after a blank line within the next 6 lines (16.2122 ... Mediterranean white dunes)
            mo = _CODE_ONLY.match(s)
            if not mo:
                continue
            name, name_at = None, i
            for k in range(i + 1, min(i + 7, len(lines))):
                t = lines[k].strip()
                if re.fullmatch(r"[A-Z][A-Z ,\-'()/]{3,}", t) or (
                        t and len(t) < 60 and not lines[k - 1].strip() and t[0].isupper()
                        and not t.endswith(".") and not t.startswith("(") and not _CODE_ONLY.match(lines[k])):
                    name, name_at = t, k
                    break
            if name is None:
                continue
            code = mo.group(1)
        code = code.replace("l", "1").replace("£", "").rstrip(".")
        if code.split(".")[0][0] not in CORINE_CHAPTERS or code in entries:
            continue
        if not (len(code.split(".")[0]) == 1 or code[:2] in {"11", "12", "13", "14", "15", "16", "17", "18", "19",
                                                             "21", "22", "23", "24"}):
            continue
        if re.search(r"\s{3,}\d+\s*$", name) or re.match(r"^[\d,]|^\((?![a-z]{3,} )", name) \
                or "biotopes manual" in name.lower():
            continue
        j = i + 1 if m else name_at + 1
        while j < len(lines) and lines[j].strip() and len(lines[j].strip()) <= 20 and not _LINE.match(lines[j]) \
                and not _CODE_ONLY.match(lines[j]) and not re.fullmatch(r"[A-Z][A-Z ,\-'()/]{3,}", lines[j].strip()):
            name += " " + lines[j].strip()
            j += 1
        notes = []
        cap = re.match(r"^([A-Z0-9][A-Z0-9 ,\-'()/]+[A-Z)])\s+([A-Z][a-z].*)$", name)
        if cap and len(cap.group(1)) > 3:
            name, syntaxon = cap.group(1), cap.group(2)
            notes.append(f"syntaxon: {syntaxon}")
        name = repair(name)
        if name.isupper():
            name = name.capitalize()
        p = pal_name.get(code)
        if p and _sim(name, p.replace("[", "").replace("]", "")) >= 0.85:
            if name != p.replace("[", "").replace("]", ""):
                notes.append(f"OCR text '{name}'; spelling as in PAL 2001")
            name = p.replace("[", "").replace("]", "")
        elif _DAMAGED.search(name):
            notes.append("OCR text, to check")
        if code in OCR_FIXES:
            fixed, syn = OCR_FIXES[code]
            notes = [f"OCR text '{name}', corrected from the page image"] + ([f"syntaxon: {syn}"] if syn else [])
            name = fixed
        entries[code] = (name, "; ".join(notes))

    for code, name in MISSING_FROM_OCR.items():
        entries.setdefault(code, (name, "missing from the OCR text layer; read on the page image"))

    def key(c: str) -> tuple[int, ...]:
        return tuple(int(x) for x in c.split("."))

    codes = sorted(entries, key=key)
    known = set(codes)
    rows = []
    for c in codes:
        # one level per digit, as in PAL: 11.121 -> 11.12 -> 11.1 -> 11 -> 1
        parent = c[:-1].rstrip(".") if len(c) > 1 else None
        while parent and parent not in known:
            parent = parent[:-1].rstrip(".") or None
        name, notes = entries[c]
        rows.append({"system": "CORINE", "code": c, "name": name,
                     "level": len(c.replace(".", "")), "parent_code": parent if parent in known else None,
                     "realm": PAL_REALM.get(c[0], ""), "group": c.split(".")[0], "description": None,
                     "source": SRC_CORINE, "notes": notes})
    out = pd.DataFrame(rows, columns=HABITATS_COLUMNS)
    out["level"] = out["level"].astype("Int64")
    return out


_RANGE = re.compile(r"^(\d{2}(?:\.[\dA-Z]+)?)\s+to\s+(\d{2}(?:\.[\dA-Z]+)?)$")


def expand_pal_expressions(crosswalks: pd.DataFrame, pal_codes: set[str]) -> pd.DataFrame:
    """Split compound PAL.CLASS expressions of the Annex I manual into their PAL codes.

    The manual writes e.g. ``16.221 to 16.227``, ``22.11 x 22.31`` (combination of two units),
    ``(22.12 or 22.15) x 22.44`` or ``42.A2 to 42.A5 and 42.A8``. Each PAL code of the expression
    becomes its own row (ranges are expanded to the PAL codes of the same level in between);
    the expression is kept in ``notes``. Codes not in PAL 2001 stay as they are (flagged later)."""
    is_pal = crosswalks.to_system == "PAL_CLASS"
    keep, new = crosswalks[~is_pal | crosswalks.to_code.isin(pal_codes)], []
    for _, r in crosswalks[is_pal & ~crosswalks.to_code.isin(pal_codes)].iterrows():
        expr = r.to_code.split("=", 1)[-1].strip()
        parts: list[str] = []
        for chunk in re.split(r"\s+(?:x|and|or)\s+|[()]", expr):
            chunk = chunk.strip()
            if not chunk:
                continue
            m = _RANGE.match(chunk)
            if m:
                a, b = m.groups()
                lvl = len(a.replace(".", ""))
                parts += sorted(c for c in pal_codes if len(c.replace(".", "")) == lvl and a <= c <= b
                                and c[:len(a) - 1] == a[:len(a) - 1])
            else:
                parts.append(chunk)
        if len(parts) <= 1 and parts == [r.to_code]:
            new.append(r.to_dict())
            continue
        for p in dict.fromkeys(parts):
            d = r.to_dict()
            d["to_code"] = p
            old = re.sub(r"compound expression as printed \('x' = combination\)(; )?", "",
                         r.notes if isinstance(r.notes, str) else "").strip("; ")
            d["notes"] = "; ".join(x for x in [old, f"from the PAL.CLASS expression '{r.to_code}' "
                                                    "('x' = combination of two units)"] if x)
            new.append(d)
    return pd.concat([keep, pd.DataFrame(new, columns=crosswalks.columns)], ignore_index=True)
