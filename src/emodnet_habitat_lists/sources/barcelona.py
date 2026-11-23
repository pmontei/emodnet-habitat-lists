"""Barcelona Convention (UNEP/MAP – SPA/RAC) classifications of Mediterranean benthic habitats.

Systems produced
----------------
``BARCELONA_2019``
    Updated Classification of Benthic Marine Habitat Types for the Mediterranean Region,
    adopted by Decision IG.24/7 (COP21, December 2019), Annex VI.
``BARCELONA_RL_2019``
    Updated Reference List of Marine Habitat Types for the Selection of Sites to be included in
    the National Inventories of Natural Sites of Conservation Interest in the Mediterranean,
    Decision IG.24/7, Annex VII. A subset of ``BARCELONA_2019``.
``BARCELONA_2006``
    Former Classification of Benthic Marine Habitat Types for the Mediterranean Region
    (adopted 1998/1999; UNEP-MAP-RAC/SPA 2006 version). Codes such as ``II.4.1.1``.

Crosswalks produced
-------------------
* ``BARCELONA_2019`` -> ``EUNIS_M_2019`` / ``EUNIS_2012`` / ``ANNEX_I`` / ``CORINE``: the
  "Reference codes for identification" of each habitat sheet of the Interpretation Manual
  (UNEP/MED WG.502/Inf.4, 2021).
* ``BARCELONA_2006`` -> ``EUNIS_M_2022``: the "Source classification system code" column of
  the EEA EUNIS marine 2022 file, where the source is a UNEP/MAP-RAC/SPA document.

There is no official correspondence between ``BARCELONA_2006`` and ``BARCELONA_2019``; see
``docs/sources.md``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ..pdftext import pdf_to_lines
from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS

# --------------------------------------------------------------------------------------------
# Source files (relative to the sources root, see docs/sources.md)
# --------------------------------------------------------------------------------------------
FOLDER = "2.Barcelona Convention"
# files are looked up by their numeric prefix, so a suffix change does not break the build
DECISION_PDF = "01_2019_*.pdf"
SPARAC_2019_PDF = "02_2019_*.pdf"
MANUAL_PDF = "03_2021_*.pdf"
OLD_2006_PDF = "05_2006_*.pdf"


def _find(sources: Path, pattern: str) -> Path:
    hits = sorted((sources / FOLDER).glob(pattern))
    if len(hits) != 1:
        raise FileNotFoundError(f"expected one file matching {FOLDER}/{pattern}, found {len(hits)}")
    return hits[0]

SRC_DECISION = "UNEP/MAP 2019, Decision IG.24/7 (UNEP/MED IG.24/22)"
SRC_MANUAL = "UNEP/MAP-SPA/RAC 2021, Interpretation Manual (UNEP/MED WG.502/Inf.4)"
SRC_2006 = "UNEP-MAP-RAC/SPA 2006, Classification of Benthic Marine Habitat Types for the Mediterranean Region"

# --------------------------------------------------------------------------------------------
# Errata: typos present in the official sources, corrected here and reported in the notes.
# key: (system, printed code, printed name prefix, code of the habitat printed just before)
# --------------------------------------------------------------------------------------------
ERRATA = {
    ("BARCELONA_2019", "ME2.512", "Facies with Brachiopoda", "MD3.511"): (
        "MD3.512",
        "Printed as ME2.512 under MD3.51 in Decision IG.24/7 and SPA/RAC 2019; corrected to MD3.512.",
    ),
    ("BARCELONA_2006", "V.2.2.10", "Facies with large Bryozoa", "IV.2.2.9"): (
        "IV.2.2.10",
        "Printed as 'V. 2. 2. 10.' under IV.2.2 in the 2006 classification; corrected to IV.2.2.10.",
    ),
}


def _apply_errata(rows: list[dict], system: str) -> None:
    for i, r in enumerate(rows):
        prev = rows[i - 1]["code"] if i else None
        for (sys_, code, name, before), (fixed, note) in ERRATA.items():
            if sys_ == system and r["code"] == code and r["name"].startswith(name) and prev == before:
                r["code"], r["notes"] = fixed, note

# ============================================================================================
# 2019 classification and reference list
# ============================================================================================
# Code grammar: M + zone letter + substrate digit + "." + region digit (5 = Mediterranean)
# + habitat digits, where facies beyond 9 use A, B, C... (MC2.51A = 10th facies of MC2.51),
# + an optional lowercase variant letter (MB1.51a, MB1.511a, MC1.51Ab).
# A few lines lack the space between code and name ("ME2.5Upper bathyal ...").
CODE_2019 = re.compile(
    r"^\s*(M[A-G]\d\.\d[0-9]*(?:[A-Z][a-z]?(?=\s)|[a-z](?=\s|[A-Z]))?)(?:\s+|(?=[A-Z]))(\S.*)$"
)
ZONES_2019 = {
    "LITTORAL", "INFRALITTORAL", "CIRCALITTORAL", "OFFSHORE CIRCALITTORAL",
    "UPPER BATHYAL", "LOWER BATHYAL", "ABYSSAL",
}
PAGE_FURNITURE = re.compile(r"^\s*(UNEP/MED IG\.24/22|Page \d+|Annex [IVX]+)\s*$")
CLASSIFICATION_START = r"^Updated Classification of Benthic Marine Habitat Types for the Mediterranean Region\s*$"
REFLIST_START = r"^Updated Reference List of Marine Habitat Types for the for the Selection"
SECTION_END = r"There are some geomorphologic"


def level_2019(code: str) -> int:
    """Hierarchical level. Level 1 = marine (M), level 2 = EUNIS zone+substrate (e.g. MA1),
    level 3 = Mediterranean region (MA1.5), then one level per character:
    ``MA1.51`` = 4, ``MA1.511`` / ``MA1.51a`` = 5, ``MB1.511a`` = 6."""
    return 2 + len(code.split(".")[1])


def parent_2019(code: str) -> str | None:
    head, tail = code.split(".")
    if len(tail) == 1:
        return None  # level-2 parent (e.g. MA1) is a EUNIS unit, not listed in the classification
    if tail[-1].islower() and len(tail) >= 4:  # MB1.511a -> MB1.51a ; MC1.51Ab -> MC1.51b
        return f"{head}.{tail[:-2]}{tail[-1]}"
    return f"{head}.{tail[:-1]}"  # MB1.51a -> MB1.51 ; MA1.511 -> MA1.51


def _parse_2019_section(lines: list[str], start: str, system: str) -> list[dict]:
    rows: list[dict] = []
    on, zone, cur = False, None, None
    for ln in lines:
        s = ln.strip()
        if not on:
            on = bool(re.search(start, ln))
            continue
        if re.search(SECTION_END, ln):
            break
        if not s or PAGE_FURNITURE.match(ln):
            continue
        if s in ZONES_2019:
            zone, cur = s, None
            continue
        m = CODE_2019.match(ln)
        if m:
            cur = {"code": m.group(1), "name": re.sub(r"\s+", " ", m.group(2)).strip(), "zone": zone, "notes": ""}
            rows.append(cur)
        elif cur is not None and s.startswith("See "):
            cur["notes"] = re.sub(r"\s+", " ", s)  # e.g. "See MC1.51b for examples of facies"
        elif cur is not None:
            cur["name"] = f"{cur['name']} {re.sub(r'\s+', ' ', s)}".strip()
    _apply_errata(rows, system)
    return rows


def load_2019(sources: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (classification, reference list) habitats from Decision IG.24/7."""
    lines = pdf_to_lines(_find(sources, DECISION_PDF))
    out = []
    for system, start in (("BARCELONA_2019", CLASSIFICATION_START), ("BARCELONA_RL_2019", REFLIST_START)):
        rows = _parse_2019_section(lines, start, "BARCELONA_2019")
        df = pd.DataFrame(rows)
        df.insert(0, "system", system)
        df["level"] = df["code"].map(level_2019).astype("Int64")
        df["parent_code"] = df["code"].map(parent_2019)
        df["realm"] = "marine"
        df["group"] = df.pop("zone").str.lower()
        df["description"] = None
        df["source"] = SRC_DECISION + (", Annex VI" if system == "BARCELONA_2019" else ", Annex VII")
        out.append(df[HABITATS_COLUMNS])
    return out[0], out[1]


def check_against_sparac(classification: pd.DataFrame, sources: Path) -> dict:
    """Compare the codes parsed from the Decision with the SPA/RAC 2019 publication."""
    codes = set()
    for ln in pdf_to_lines(_find(sources, SPARAC_2019_PDF)):
        m = CODE_2019.match(ln)
        if m:
            codes.add(m.group(1))
    parsed = set(classification["code"])
    # the SPA/RAC publication carries the same ME2.512 typo
    codes = {("MD3.512" if c == "ME2.512" else c) for c in codes} | ({"ME2.512"} & parsed)
    return {"only_in_decision": sorted(parsed - codes), "only_in_sparac": sorted(codes - parsed)}


# ============================================================================================
# 2006 (former) classification
# ============================================================================================
LEVEL1_2006 = re.compile(r"^\s*([IVX]+)\.\s+([A-Z][A-Z ]+)\s*$")
CODE_2006 = re.compile(r"^\s*([IVX]+\.(?:\s?\d+\.?)+)\s+(\S.*)$")
STAGES_2006 = {"I": "supralittoral", "II": "mediolittoral", "III": "infralittoral",
               "IV": "circalittoral", "V": "bathyal", "VI": "abyssal"}


def normalise_code_2006(code: str) -> str:
    """``'II. 4. 1. 1.'`` -> ``'II.4.1.1'``; also used to normalise codes cited elsewhere."""
    return re.sub(r"\s+", "", code).rstrip(".")


def load_2006(sources: Path) -> pd.DataFrame:
    rows: list[dict] = []
    on, cur = False, None
    for ln in pdf_to_lines(_find(sources, OLD_2006_PDF)):
        s = ln.strip()
        m1 = LEVEL1_2006.match(ln)
        if m1 and m1.group(1) in STAGES_2006:
            on = True
            cur = {"code": m1.group(1), "name": m1.group(2).strip(), "notes": ""}
            rows.append(cur)
            continue
        if not on or not s:
            continue
        m = CODE_2006.match(ln)
        if m:
            name = re.sub(r"\s+", " ", m.group(2)).strip().rstrip(" :")
            cur = {"code": normalise_code_2006(m.group(1)), "name": name, "notes": ""}
            rows.append(cur)
        elif cur is not None and ln.startswith(" ") and not s.isupper():
            cur["name"] = f"{cur['name']} {re.sub(r'\s+', ' ', s)}"
        else:
            cur = None
    _apply_errata(rows, "BARCELONA_2006")
    df = pd.DataFrame(rows).drop_duplicates("code")
    df.insert(0, "system", "BARCELONA_2006")
    df["level"] = df["code"].str.count(r"\.").add(1).astype("Int64")
    df["parent_code"] = df["code"].map(lambda c: c.rsplit(".", 1)[0] if "." in c else None)
    df["realm"] = "marine"
    df["group"] = df["code"].str.split(".").str[0].map(STAGES_2006)
    df["description"] = None
    df["source"] = SRC_2006
    return df[HABITATS_COLUMNS]


# ============================================================================================
# Crosswalks
# ============================================================================================
MANUAL_FIELDS = {
    "EUNIS 2019": "EUNIS_M_2019",
    "EUNIS 2017": "EUNIS_M_2019",  # one sheet prints "EUNIS 2017"
    "EUNIS 2007": "EUNIS_2012",
    "EC": "ANNEX_I",
    "CORINE": "CORINE",
}
CODE_PATTERNS = {
    "BARCELONA CONVENTION": r"M[A-G]\d\.\d[0-9]*(?:[A-Z][a-z]?|[a-z])?",
    "EUNIS_M_2019": r"M[A-H][0-9A-Z]{1,6}",
    "EUNIS_2012": r"[A-J][0-9A-Z]?\.?[0-9A-Za-z.]*",
    "ANNEX_I": r"\d{4}\*?",
    "CORINE": r"\d{2}(?:\.\d+)*",
}
_BULLET = re.compile(r"^•\s*([A-Z][A-Z0-9 ]+?)\s*:\s*(.*)$")
_PROSE = re.compile(r"[a-z]{3,}\s+[a-z]{3,}")  # two lowercase words in a row = description text


def _tokens(text: str, pattern: str) -> list[tuple[str, bool]]:
    """Codes found in ``text`` with a flag for a following '(partim)'."""
    out = []
    for m in re.finditer(rf"(?<![A-Za-z0-9.])({pattern})(?![A-Za-z0-9])(\s*\(partim\))?", text):
        out.append((m.group(1).rstrip("."), bool(m.group(2))))
    return out


def crosswalk_manual(sources: Path) -> pd.DataFrame:
    """Reference codes of each habitat sheet of the Interpretation Manual (2021).

    Each sheet starts with a box "Reference codes for identification" listing the habitat's
    code in the Barcelona Convention classification and its EUNIS 2019, EUNIS 2007, Habitats
    Directive (EC) and, sometimes, CORINE codes, optionally followed by "(partim)".
    """
    lines = [l.strip() for l in pdf_to_lines(_find(sources, MANUAL_PDF), layout=False)]
    rows = []
    i = 0
    while i < len(lines):
        if not re.match(r"^•\s*BARCELONA CONVENTION:", lines[i]):
            i += 1
            continue
        block: dict[str, str] = {"BARCELONA CONVENTION": lines[i].split(":", 1)[1]}
        field: str | None = "BARCELONA CONVENTION"
        j = i + 1
        while j < len(lines) and not lines[j].startswith("LOCATION OF THE HABITAT") and j - i < 40:
            ln = lines[j]
            mb = _BULLET.match(ln)
            if mb:
                field = mb.group(1).strip()
                block[field] = mb.group(2)
            elif ln.startswith("Description of the habitat") or _PROSE.search(ln.replace("partim", "")):
                field = None
            elif ln and field:
                block[field] = f"{block[field]} {ln}"
            j += 1
        bc_codes = [c for c, _ in _tokens(block["BARCELONA CONVENTION"], CODE_PATTERNS["BARCELONA CONVENTION"])]
        for fld, target in MANUAL_FIELDS.items():
            for code, partim in _tokens(block.get(fld, ""), CODE_PATTERNS[target]):
                for bc in bc_codes:
                    rows.append({
                        "from_system": "BARCELONA_2019", "from_code": bc,
                        "to_system": target, "to_code": code,
                        "relationship": "partim" if partim else "unspecified",
                        "source": SRC_MANUAL + ", habitat sheet reference codes",
                        "notes": "printed as 'EUNIS 2007'" if fld == "EUNIS 2007" else "",
                    })
        i = j
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()


def crosswalk_eunis2022_sources(eunis_m_2022_xlsx: Path) -> pd.DataFrame:
    """BARCELONA_2006 -> EUNIS_M_2022 from the EEA 'Source classification system code' column."""
    df = pd.read_excel(eunis_m_2022_xlsx, sheet_name="Benthic habitats", dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    sel = df[df["Source classification system name"].fillna("").str.contains("RAC/SPA|RAC-SPA|SPA/RAC")]
    rows = []
    for _, r in sel.iterrows():
        for raw in re.split(r"[;\n]", str(r["Source classification system code"])):
            raw = raw.strip()
            if not raw or raw == "nan":
                continue
            code = normalise_code_2006(raw)
            note = ""
            if re.match(r"^11\.", code):  # typo in the EEA file: '11.4.1.4' for 'II.4.1.4'
                note = f"printed as '{raw}' in the EEA file"
                code = "II." + code[3:]
            elif re.match(r"^[IVX]+\d", code):  # typo in the EEA file: 'III1.1' for 'III.1.1'
                note = f"printed as '{raw}' in the EEA file"
                code = re.sub(r"^([IVX]+)(\d)", r"\1.\2", code)
            if not re.match(r"^[IVX]+(\.\d+)+$", code):
                continue  # EUNIS 2004 codes cited in mixed-source rows, not Barcelona codes
            rows.append({
                "from_system": "BARCELONA_2006", "from_code": code,
                "to_system": "EUNIS_M_2022", "to_code": str(r["Code"]).strip(),
                "relationship": "source of",
                "source": f"EEA 2022, EUNIS marine habitat classification 2022 including crosswalks, "
                          f"'Source classification system code' ({str(r['Source classification system name']).strip()})",
                "notes": note,
            })
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()


def habitats(sources: Path) -> pd.DataFrame:
    cl, rl = load_2019(sources)
    old = load_2006(sources)
    return pd.concat([cl, rl, old], ignore_index=True)


# --------------------------------------------------------------------------------------------
# 2006 <-> 2019: no official correspondence exists. Two kinds of indicative rows are provided.
# --------------------------------------------------------------------------------------------
# (1) Pairs published by SPA/RAC in a national report, which states that no handbook or guide
#     exists to compare the former list with the new classification ("indicative").
SRC_IONIAN = (
    "SPA/RAC, Italian Ionian / Central Mediterranean Sea subregion: conservation of Mediterranean "
    "marine and coastal biodiversity by 2030 and beyond, section 2.2 "
    "(https://spa-rac.org/italian-ionian-central-mediterranean-sea-subregion-conservation-of-"
    "mediterranean-marine-and-coastal-biodiversity-by-2030-and-beyond/)"
)
PUBLISHED_2006_2019 = [
    ("III.1.1", "MB5.54"),
    ("III.5", "MB2.54"),
    ("II.4.1", "MA1.53"),
    ("II.4.2", "MA1.54"),
    ("III.6.1", "MB1.51"),
    ("IV.3.1", "MC1.51"),
]


def crosswalk_2006_2019_published() -> pd.DataFrame:
    rows = [{
        "from_system": "BARCELONA_2006", "from_code": a, "to_system": "BARCELONA_2019", "to_code": b,
        "relationship": "indicative", "source": SRC_IONIAN,
        "notes": "Published as indicative; no official correspondence exists.",
    } for a, b in PUBLISHED_2006_2019]
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


def crosswalk_2006_2019_candidates(
    old_to_eunis22: pd.DataFrame, manual: pd.DataFrame, habitats: pd.DataFrame
) -> pd.DataFrame:
    """(2) Candidate pairs derived through EUNIS: a 2006 code that is the EEA source of EUNIS
    marine 2022 habitat E, and a 2019 code whose Interpretation Manual sheet cites E as its
    EUNIS 2019 code (E must have the same code and name in EUNIS 2019 and 2022).
    These are candidates for expert review, not correspondences."""
    e = habitats[habitats["system"].isin(["EUNIS_M_2019", "EUNIS_M_2022"])]
    names = e.pivot_table(index="code", columns="system", values="name", aggfunc="first")
    stable = set(names.index[names["EUNIS_M_2019"] == names["EUNIS_M_2022"]])
    m = manual[manual["to_system"] == "EUNIS_M_2019"]
    j = old_to_eunis22.merge(m, on="to_code", suffixes=("_06", "_19"))
    j = j[j["to_code"].isin(stable)]
    rows = [{
        "from_system": "BARCELONA_2006", "from_code": r.from_code_06,
        "to_system": "BARCELONA_2019", "to_code": r.from_code_19,
        "relationship": "candidate",
        "source": "Derived: EEA EUNIS marine 2022 source codes x Interpretation Manual 2021 reference codes",
        "notes": f"via EUNIS {r.to_code}"
                 + (" (manual: partim)" if r.relationship_19 == "partim" else "")
                 + "; to be reviewed by experts",
    } for r in j.itertuples()]
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()
