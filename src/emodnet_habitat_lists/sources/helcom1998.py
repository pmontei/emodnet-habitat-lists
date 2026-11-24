"""HELCOM 1998 classification of marine and coastal biotopes of the Baltic Sea (BSEP 75).

Source: HELCOM, 1998. Red List of marine and coastal biotopes and biotope complexes of the Baltic
Sea, Belt Sea and Kattegat, including a comprehensive description and classification system for
all Baltic marine and coastal biotopes. Baltic Sea Environment Proceedings No. 75.

System produced
---------------
``HELCOM_1998``: the numbered biotopes of Table 5 "Red list and threat evaluation of marine and
coastal biotopes" (1 pelagic, 2 benthic marine, 3 terrestrial coastal, 4 coastal lakes and pools,
5 riverine). ``parent_code`` drops the last number. The national threat categories are not loaded.

Parsing: each entry of Table 5 is a block of lines with one code at the left margin; the name may
wrap above and below the code line. Country/threat columns and impact abbreviations are removed.

Known issues of the copy in the source folder (doczz.net 6196077)
-----------------------------------------------------------------
* Printed page 102 is missing: page 102 of the PDF repeats page 101. The entries of that page
  (``2.2.3.3`` to ``2.4.2.3``, stony reefs of the hydrolittoral, hard clay and gravel bottoms) are
  taken from the alphabetical lists of the same chapter (Red lists by threat category,
  pp. 95-97) and, for the headings, from the description chapter (pp. 72-73): ``MISSING_PAGE``.
  The tests check every name against the PDF text.
* Three names are cut in the table layout; their full names come from the same lists:
  ``NAME_FIXES``.
* The biotope complexes (letter codes A-J) are not loaded.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ..pdftext import pdf_to_lines
from ..schema import HABITATS_COLUMNS

FOLDER = "3.HELCOM HUB"
PDF_GLOBS = ("*1998*HELCOM*BSEP75*.pdf", "*BSEP75*.pdf", "*BSEP-75*.pdf", "6196077.pdf")
SRC = ("HELCOM, 1998. Red List of marine and coastal biotopes and biotope complexes of the Baltic Sea, "
       "Belt Sea and Kattegat. Baltic Sea Environment Proceedings No. 75, Table 5")

MISSING_PAGE = {   # code -> (name, where it is printed)
    "2.2.3.3": ("Stony reefs of the hydrolittoral with or without macrophyte vegetation", "Red lists, p. 96"),
    "2.3": ("Hard clay bottoms", "description chapter, p. 73"),
    "2.3.1": ("Hard clay bottoms of the aphotic zone", "Red lists, p. 96"),
    "2.3.2": ("Sublittoral photic zone", "description chapter, p. 73"),
    "2.3.2.1": ("Sublittoral hard clay bottoms with little or no macrophyte vegetation of the photic zone",
                "Red lists, p. 96"),
    "2.3.3": ("Hydrolittoral", "description chapter, p. 73"),
    "2.3.3.1": ("Hydrolittoral hard clay bottoms with little or no macrophyte vegetation", "Red lists, p. 96"),
    "2.4": ("Gravel bottoms", "description chapter, p. 73"),
    "2.4.1": ("Gravel bottoms of the aphotic zone", "Red lists, p. 96"),
    "2.4.2": ("Sublittoral photic zone", "description chapter, p. 73"),
    "2.4.2.1": ("Sublittoral level gravel bottoms with little or no macrophyte vegetation of the photic zone",
                "Red lists, p. 96"),
    "2.4.2.2": ("Sublittoral level gravel bottoms dominated by macrophyte vegetation", "Red lists, p. 96"),
    "2.4.2.3": ("Sublittoral gravel banks of the photic zone with or without macrophyte vegetation",
                "Red lists, p. 96"),
}
NAME_FIXES = {
    "2.7.2.1": "Sublittoral muddy bottoms with little or no macrophyte vegetation of the photic zone",
    "3.5.1.1": "Gently sloping limestone shores with no or low vegetation",
    "3.6.2.1": "Sandstone cliffs with no or low vegetation",
    "3.1": "Spits/bars",
}
GROUPS = {"1": ("marine", "pelagic"), "2": ("marine", "benthic"), "3": ("terrestrial", "coastal"),
          "4": ("freshwater", "coastal lakes and pools"), "5": ("freshwater", "riverine")}

_CODE = re.compile(r"^\s{0,2}(\d(?:\.\d+)*)\s")
_DROP_TOKEN = re.compile(r"^(?:X|P|p|CP|CW|EST|RUPE,?|[A-Z]{1,6}(?:,[A-Z]{1,6})+,?|[A-Z]{1,6},)$")
_HEADER = ("DK", "SWE", "FIN", "RUPe", "RU Pe", "EST", "LAT", "LIT", "RUKa", "RU Ka", "POL", "GER", "Major",
           "human", "impacts", "DE", "QU", "Code", "Biotope type")


def find_pdf(sources: Path) -> Path | None:
    for g in PDF_GLOBS:
        files = sorted((sources / FOLDER).glob(g))
        if files:
            return files[0]
    return None


def _fragments(line: str) -> list[str]:
    out = []
    for chunk in re.split(r"\s{2,}", line.strip()):
        if not chunk or re.fullmatch(r"[\d\-\*\?P]+(?:\s[\d\-\*\?P]+)*", chunk):
            continue
        if re.fullmatch(r"[A-Z]{2,}[A-Za-z]*(?:,[A-Z]+[A-Za-z]*)*,?", chunk):          # impact abbreviations
            continue
        if chunk.startswith(_HEADER) or "Red List of Biotopes" in chunk or \
                chunk.startswith(("Table 5", "OF THE BALTIC", "(for abbreviations")) or chunk.isdigit():
            continue
        out.append(chunk)
    return out


def _clean(name: str) -> str:
    words = [w for w in name.split() if not _DROP_TOKEN.match(w)]
    return re.sub(r"\s+", " ", " ".join(words)).strip()


def habitats(sources: Path) -> pd.DataFrame:
    pdf = find_pdf(sources)
    if pdf is None:
        raise FileNotFoundError(f"{sources / FOLDER}: HELCOM BSEP 75 PDF not found")
    lines = pdf_to_lines(pdf)
    start = next(i for i, s in enumerate(lines) if "Table 5: RED LIST AND THREAT EVALUATION" in s)
    end = next(i for i in range(start, len(lines))
               if "BALTIC SEA ENVIRONMENT PROCEEDINGS" in lines[i] or lines[i].startswith("No. "))
    blocks, cur = [], []
    for s in lines[start:end]:
        s = s.replace("\f", "")
        if not s.strip():
            if cur:
                blocks.append(cur)
                cur = []
            continue
        cur.append(s)
    if cur:
        blocks.append(cur)

    entries: dict[str, tuple[str, str]] = {}
    for b in blocks:
        codes = [(j, _CODE.match(x).group(1)) for j, x in enumerate(b) if _CODE.match(x)]
        for k, (j, code) in enumerate(codes):
            lo = codes[k - 1][0] + 1 if k else 0
            hi = codes[k + 1][0] if k + 1 < len(codes) else len(b)
            parts = []
            for jj in range(lo, hi):
                line = b[jj][_CODE.match(b[jj]).end():] if jj == j else b[jj]
                parts += _fragments(line)
            if code not in entries:          # the duplicated page repeats entries
                text = " ".join(parts)
                entries[code] = (_clean(text) if "." in code else re.sub(r"\s+", " ", text).strip(), "")
    for code, name in NAME_FIXES.items():
        if code in entries:
            entries[code] = (name, f"name cut in the table layout; full name from the Red lists (pp. 95-97); "
                                   f"table text: '{entries[code][0]}'")
    for code, (name, where) in MISSING_PAGE.items():
        entries.setdefault(code, (name, f"page 102 of Table 5 missing in the source copy; name from {where}"))

    def key(c: str) -> tuple[int, ...]:
        return tuple(int(x) for x in c.split("."))

    rows = []
    for code in sorted(entries, key=key):
        name, note = entries[code]
        realm, group = GROUPS.get(code.split(".")[0], ("", ""))
        rows.append({"system": "HELCOM_1998", "code": code, "name": name, "level": code.count(".") + 1,
                     "parent_code": code.rsplit(".", 1)[0] if "." in code else None, "realm": realm,
                     "group": group, "description": None, "source": SRC, "notes": note})
    out = pd.DataFrame(rows, columns=HABITATS_COLUMNS)
    out["level"] = out["level"].astype("Int64")
    return out
