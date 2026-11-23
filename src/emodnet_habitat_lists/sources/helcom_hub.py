"""HELCOM HUB – HELCOM Underwater Biotope and habitat classification (Baltic Sea).

System produced
---------------
``HELCOM_HUB``
    * the 328 units of Annex 1 "Complete list of HUB biotopes" of BSEP 139 (HELCOM 2013):
      207 photic and 115 aphotic benthic biotopes, 1 sea-ice habitat and 5 pelagic habitats;
    * the higher levels of the hierarchy (``A``, ``AA``, ``AA.A``, ``AA.A1`` ...), named after the
      HELCOM HUB fact sheets;
    * the 10 biotope complexes (Habitats Directive Annex I codes, e.g. ``1110``), group
      ``biotope complex``.
    The HELCOM Red List category (BSEP 138, Annex 2) is added to ``notes``.

Levels: ``A`` = 1 (Baltic), ``AA`` = 2, ``AA.A`` = 3, ``AA.A1`` = 4, ``AA.A1C`` = 5, ``AA.A1C1`` = 6.

Crosswalks produced
-------------------
* ``HELCOM_HUB`` -> ``EUNIS_2012`` and ``HELCOM_1998``: "Correspondence with other classification
  systems" of each fact sheet (most specific codes only).
* ``HELCOM_HUB`` -> ``EUNIS_M_2022``: EEA "Source classification system code" column (HELCOM HUB 2013).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ..pdftext import pdf_to_lines
from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS

FOLDER = "3.HELCOM HUB"
BSEP139 = "01_2013_*BSEP139*.pdf"
BSEP138 = "02_2013_*BSEP138*.pdf"
FACT_SHEETS = "fact sheets"
SRC_139 = "HELCOM 2013, HELCOM HUB Technical Report, BSEP 139, Annex 1"
SRC_138 = "HELCOM 2013, Red List of Baltic Sea underwater biotopes, habitats and biotope complexes, BSEP 138, Annex 2"
SRC_FS = "HELCOM HUB fact sheet"

# Fact sheets published under a code that does not match the biotope in BSEP 139
FACT_SHEET_ERRATA = {
    "AB.H3M6": ("AB.H3M5", "fact sheet (and BSEP 138) code AB.H3M6; the code is AB.H3M5 in BSEP 139 Annex 1"),
    "AB.J2K7": ("AB.J3L7", "fact sheet file named AB.J2K7; the biotope is AB.J3L7 in BSEP 139"),
}

HUB_CODE = r"A[A-E](?:\.[A-Z](?:\d(?:[A-Z]\d*)?)?)?"
LINE_139 = re.compile(rf"(?:^|\s)({HUB_CODE}|AC)\s+(Baltic\b.*)$")
COMPLEX = re.compile(r"^\s*(1[1-6][1-9]0)\s+(\S.*)$")
# "... name    EN   B1+2a(ii)   M"  -> category, criterion, confidence (columns separated by 2+ spaces)
RL_CAT = re.compile(r"\s{2,}(CR|EN|VU|NT|LC|DD|NE|RE|NA)(?:\s{2,}(\S(?:.*?\S)?))??(?:\s{2,}([HML]))?\s*$")


def _find(sources: Path, pattern: str) -> Path:
    hits = sorted((sources / FOLDER).glob(pattern))
    if len(hits) != 1:
        raise FileNotFoundError(f"expected one file matching {FOLDER}/{pattern}, found {len(hits)}")
    return hits[0]


def level(code: str) -> int:
    if code == "A":
        return 1
    if len(code) == 2:
        return 2
    tail = code.split(".", 1)[1]
    if len(tail) == 1:
        return 3
    if len(tail) == 2:
        return 4
    if len(tail) == 3:
        return 5
    return 6


def parent(code: str) -> str | None:
    if code == "A":
        return None
    if len(code) == 2:
        return "A"
    head, tail = code.split(".", 1)
    if len(tail) == 1:
        return head
    if len(tail) <= 3:
        return f"{head}.{tail[:-1]}"
    return f"{head}.{tail[:3]}"  # level 6 (AA.A1C1, AB.I3L10) -> level 5


def _sentence_case(s: str) -> str:
    return s[:1] + s[1:].lower() if s.isupper() else s


def annex1(sources: Path) -> tuple[list[dict], list[dict]]:
    lines = pdf_to_lines(_find(sources, BSEP139))
    start = max(i for i, l in enumerate(lines) if l.strip().startswith("Annex 1. Complete list of HUB biotopes"))
    end = max(i for i, l in enumerate(lines) if l.strip().startswith("Annex 2. Comparison"))
    units, complexes, cur, in_complex = [], [], None, False
    for ln in lines[start:end]:
        s = ln.strip()
        if not s or s in {"HELCOM HUB", "Table continues"} or re.fullmatch(r"\d+", s):
            continue
        if s.startswith("HUB Biotope Complexes"):
            in_complex, cur = True, None
            continue
        if in_complex:
            m = COMPLEX.match(ln)
            if m:
                cur = {"code": m.group(1), "name": m.group(2).strip()}
                complexes.append(cur)
            elif cur is not None and len(ln) - len(ln.lstrip()) > 6:
                cur["name"] += " " + s
            continue
        m = LINE_139.search(ln)
        if m:
            cur = {"code": m.group(1), "name": re.sub(r"\s+", " ", m.group(2)).strip()}
            units.append(cur)
        elif cur is not None and len(ln) - len(ln.lstrip()) >= 15 and not re.match(r"^(\d|X\b)", s):
            cur["name"] = f"{cur['name']} {re.sub(r'\s+', ' ', s)}"
        else:
            cur = None
    return units, complexes


def red_list(sources: Path) -> dict[str, tuple[str, str, str]]:
    """{code as printed in BSEP 138: (category, criterion, name start)}"""
    lines = pdf_to_lines(_find(sources, BSEP138))
    start = max(i for i, l in enumerate(lines) if l.strip().startswith("Annex 2. Complete list of all considered"))
    end = max(i for i, l in enumerate(lines) if l.strip().startswith("Annex 3. Questionnaire"))
    out, cur, name = {}, None, ""
    for ln in lines[start:end]:
        # a page number is sometimes glued to the left of a line ("58  AA.H3L3 ...")
        m = re.match(rf"^\s*(?:\d+\s+)?({HUB_CODE}|AC)\s+(.*)$", ln)
        if m:
            cur, name = m.group(1), RL_CAT.sub("", m.group(2)).strip()
        c = RL_CAT.search(ln)
        if c and cur and cur not in out:
            crit = (c.group(2) or "").strip()
            if crit in {"H", "M", "L"}:
                crit = ""
            out[cur] = (c.group(1), crit, name)
    # biotope complexes: Table 13 (columns: code, name, category, confidence, criterion)
    t13 = max(i for i, l in enumerate(lines) if l.strip().startswith("Table 13. HELCOM Red List of Baltic Sea biotope complexes"))
    for ln in lines[t13:t13 + 25]:
        m = re.match(r"^\s*(1[1-6][1-9]0)\s+(.+?)\s{2,}(CR|EN|VU|NT|LC|DD|NE)\s+([HML])\s+(\S+)\s*$", ln)
        if m:
            out[m.group(1)] = (m.group(3), m.group(5), m.group(2))
    return out


def _norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower().replace("characterized", "characterised"))[:60]


def fact_sheet_titles(sources: Path) -> dict[str, tuple[str, Path]]:
    out = {}
    for pdf in sorted((sources / FOLDER / FACT_SHEETS).glob("*.pdf")):
        file_code = pdf.stem.strip()
        code = FACT_SHEET_ERRATA.get(file_code, (file_code, ""))[0]
        lines = [l.strip() for l in pdf_to_lines(pdf, layout=False) if l.strip()]
        title = []
        for l in lines[:6]:
            if l.upper() in {"AUTHOR", "TEXTUAL DESCRIPTION"}:
                break
            title.append(l)
        name = " ".join(title)
        name = re.sub(rf"^{re.escape(file_code)}\s*", "", name).strip()
        out[code] = (_sentence_case(name), pdf)
    return out


def habitats(sources: Path) -> pd.DataFrame:
    units, complexes = annex1(sources)
    rl = red_list(sources)
    titles = fact_sheet_titles(sources)
    rows, seen = [], set()

    # BSEP 138 uses a different code for a few biotopes: match those by name
    annex_codes = {u["code"] for u in units}
    by_name = {_norm(u["name"]): u["code"] for u in units}
    rl_by_code = {}
    for rc, (cat, crit, nm) in rl.items():
        target, note = rc, ""
        if rc not in annex_codes and not rc[0].isdigit():
            target = by_name.get(_norm(nm), rc)
            if target != rc:
                note = f"; coded {rc} in BSEP 138"
        rl_by_code[target] = (cat, crit, note)

    def rl_note(code):
        if code in rl_by_code:
            cat, crit, note = rl_by_code[code]
            return f"HELCOM Red List 2013: {cat}" + (f" ({crit})" if crit else "") + note
        return ""

    for u in units:
        if u["code"] in seen:
            continue
        seen.add(u["code"])
        rows.append({"code": u["code"], "name": u["name"], "group": "biotope/habitat", "source": SRC_139,
                     "notes": rl_note(u["code"])})
    for code, (name, pdf) in titles.items():
        if code in seen:
            continue
        seen.add(code)
        rows.append({"code": code, "name": name, "group": "higher level", "source": f"{SRC_FS} {pdf.name}",
                     "notes": "not in BSEP 139 Annex 1 (higher level of the hierarchy)"})
    for c in complexes:
        rows.append({"code": c["code"], "name": c["name"], "group": "biotope complex",
                     "source": SRC_139 + " (biotope complexes = Habitats Directive Annex I codes)",
                     "notes": rl_note(c["code"])})
    df = pd.DataFrame(rows)
    df.insert(0, "system", "HELCOM_HUB")
    is_cx = df["group"] == "biotope complex"
    df["level"] = [None if cx else level(c) for c, cx in zip(df["code"], is_cx)]
    df["level"] = df["level"].astype("Int64")
    df["parent_code"] = [None if cx else parent(c) for c, cx in zip(df["code"], is_cx)]
    df["realm"] = "marine"
    df["description"] = None
    return df[HABITATS_COLUMNS]


# ---------------------------------------------------------------------------------------------
def _leaves(codes: list[str]) -> list[str]:
    """Most specific codes of a path listing (drop codes that are a prefix of another)."""
    return [c for c in codes if not any(o != c and o.startswith(c) for o in codes)]


def crosswalk_fact_sheets(sources: Path) -> pd.DataFrame:
    rows = []
    for pdf in sorted((sources / FOLDER / FACT_SHEETS).glob("*.pdf")):
        file_code = pdf.stem.strip()
        code, err = FACT_SHEET_ERRATA.get(file_code, (file_code, ""))
        lines = [l.strip() for l in pdf_to_lines(pdf, layout=False)]
        try:
            k = next(i for i, l in enumerate(lines) if l.upper().startswith("CORRESPONDENCE WITH OTHER CLASSIFICATION"))
        except StopIteration:
            continue
        block, field = {"HELCOM 1998": [], "EUNIS 2012": []}, None
        for l in lines[k + 1:]:
            u = l.upper()
            if u.startswith("HELCOM 1998"):
                field = "HELCOM 1998"
                continue
            if u.startswith("EUNIS 2012"):
                field = "EUNIS 2012"
                continue
            if field is None or not l or l.startswith("http"):
                continue
            if field == "HELCOM 1998":
                m = re.match(r"^(\d(?:\.\d+)+)\s", l)
                if m:
                    block[field].append(m.group(1))
                elif re.match(r"^[A-Z][A-Z ]{6,}$", l):
                    field = None
            else:
                m = re.match(r"^([A-J]\d?(?:\.[0-9A-Z]+)?)\s*:?\s+\S", l)
                if m:
                    block[field].append(m.group(1))
                elif re.match(r"^[A-Z][A-Z ]{6,}$", l):
                    field = None
        for fld, target in (("HELCOM 1998", "HELCOM_1998"), ("EUNIS 2012", "EUNIS_2012")):
            for c in _leaves(list(dict.fromkeys(block[fld]))):
                rows.append({"from_system": "HELCOM_HUB", "from_code": code, "to_system": target, "to_code": c,
                             "relationship": "unspecified", "source": f"{SRC_FS} {pdf.name}",
                             "notes": "; ".join(x for x in (err, "most specific code of the path listed in the fact sheet") if x)})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()


def crosswalk_eunis2022_sources(eunis_m_2022_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(eunis_m_2022_xlsx, sheet_name="Benthic habitats", dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    sel = df[df["Source classification system name"].fillna("").str.contains("HELCOM")]
    rows = []
    for _, r in sel.iterrows():
        for raw in re.split(r"[;,\n]", str(r["Source classification system code"])):
            # values look like 'AA.A 1C1(modified)', 'AA.A 1C5modified)': drop the qualifier and spaces
            modified = "modified" in raw
            c = re.sub(r"\(?modified\)?", "", raw).replace(" ", "").strip()
            if not re.fullmatch(HUB_CODE, c):
                continue
            rows.append({"from_system": "HELCOM_HUB", "from_code": c, "to_system": "EUNIS_M_2022",
                         "to_code": str(r["Code"]).strip(),
                         "relationship": "source of (modified)" if modified else "source of",
                         "source": "EEA 2022, EUNIS marine habitat classification 2022 including crosswalks, "
                                   "'Source classification system code' (HELCOM HUB (2013))",
                         "notes": f"printed as '{raw.strip()}' in the EEA file" if raw.strip() != c + "(modified)" and raw.strip() != c else ""})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()
