"""European Red List of Habitats (2016), Part 1: marine habitats.

System produced
---------------
``EU_REDLIST_2016``
    The 257 benthic habitat types assessed (Annex A of the report), with their EU28 and EU28+
    categories and criteria in ``notes``. Codes are those of the EEA publication: the sea prefix
    (``BAL``, ``NEA``, ``MED``, ``BLS``) followed by the Red List code printed in Annex A (the
    habitat number for the Baltic, a provisional EUNIS-like level-4 code elsewhere), e.g.
    ``BAL21``, ``NEAA5.25``, ``BLSA5.5w`` (see "Codes" below). Level 1 rows are the four seas.

Crosswalk produced
------------------
``EUNIS_M_2022 -> EU_REDLIST_2016``: columns "Red List relationship" / "Red List code (for EEA
publication)" of the EEA file "EUNIS marine habitat classification 2022 including crosswalks".
Relationships as given (``<``, ``>``, ``≈``).

Codes: Annex A prints working codes that are not unique (``A5.62`` twice in the North-East Atlantic,
``A3.2x`` twice in the Black Sea ...). The repository uses the EEA "code for EEA publication"
(``NEAA1.25``, ``NEAA5.67`` ...), assigned to each Annex A row by sea, working code and name; the
Annex A code is kept in ``notes``.
"""

from __future__ import annotations

import difflib
import re
from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS

FOLDER = "14.European Red List of Habitats"
REPORT_GLOB = "*[Pp]art*1*[Mm]arine*.pdf"
SRC = ("Gubbay, S., Sanders, N., Haynes, T. et al., 2016. European Red List of Habitats. Part 1. Marine habitats. "
       "European Commission, doi:10.2779/032638")
SRC_EEA = ("EEA 2022, EUNIS marine habitat classification 2022 including crosswalks, sheet 'Benthic habitats', "
           "columns 'Red List relationship' / 'Red List code (for EEA publication)'")
SEAS = {"A.1": ("BAL", "Baltic Sea"), "A.2": ("NEA", "North-East Atlantic"), "A.3": ("MED", "Mediterranean Sea"),
        "A.4": ("BLS", "Black Sea")}
CAT = r"CR|EN|VU|NT|LC|DD|N/A|NE|CO"
_ROW = re.compile(rf"^\s*(\S+)\s{{2,}}(\S.*?)\s+({CAT})\s+({CAT})(?:\s+(.*))?$")


def _pdf(sources: Path) -> Path:
    files = sorted((sources / FOLDER).glob(REPORT_GLOB))
    if not files:
        raise FileNotFoundError(f"{sources / FOLDER}/{REPORT_GLOB}")
    return files[0]


def annex_a(sources: Path) -> list[dict]:
    lines = "\n".join(pdftext.pdf_to_lines(_pdf(sources))).replace("\f", "\n").split("\n")
    a = [i for i, l in enumerate(lines) if l.strip().startswith("Annex A") and "Lists of EUNIS" in l][-1]
    b = next(i for i in range(a, len(lines)) if lines[i].strip().startswith("Annex B"))
    sea = None
    out: list[dict] = []
    cat_col = None
    for line in lines[a:b]:
        s = line.strip()
        if m := re.match(r"^(A\.[1-4]) ", s):
            sea = SEAS[m.group(1)]
            continue
        if not s or sea is None or re.match(r"^(Habitat|number|ENUIS|EUNIS|CODE|EU28|\d+\s+European Red List)", s) \
                or "European Red List of Habitats" in s or s.startswith(("#", "*")):
            continue
        if m := _ROW.match(line):
            cat_col = line.index(m.group(3), m.end(2))
            crit = [c.strip() for c in re.split(r"\s{2,}", (m.group(5) or "").strip())] + ["", ""]
            if crit[0] and not crit[1]:          # both criteria separated by one space only
                first = crit[0].split()[0]
                k = crit[0].find(" " + first, len(first))
                if k > 0:
                    crit[0], crit[1] = crit[0][:k].strip(), crit[0][k:].strip()
            c1 = m.start(5) if m.group(5) else None
            c2 = line.find(crit[1], c1 + len(crit[0])) if c1 is not None and crit[1] else None
            out.append({"sea": sea, "rl_code": m.group(1), "name": m.group(2).strip(), "eu28": m.group(3),
                        "eu28p": m.group(4), "crit28": crit[0], "crit28p": crit[1], "cols": (c1, c2)})
        elif out and cat_col:
            left = line[:cat_col].strip()
            if left:
                out[-1]["name"] += " " + left
            c1, c2 = out[-1]["cols"]
            if c1 is not None and c2 is not None and len(line) > c1 - 2:     # wrapped criteria
                a1, a2 = line[c1 - 2:c2 - 2].strip(), line[c2 - 2:].strip()
                if a1 and out[-1]["crit28"].endswith(("/", ",")):
                    out[-1]["crit28"] += ("" if out[-1]["crit28"].endswith("/") else " ") + a1
                if a2 and out[-1]["crit28p"].endswith(("/", ",")):
                    out[-1]["crit28p"] += ("" if out[-1]["crit28p"].endswith("/") else " ") + a2
    for r in out:
        r["name"] = re.sub(r"\s+", " ", r["name"]).strip()
        if r["rl_code"] == "-":                       # Marmara habitat printed without a code
            r["code"] = r["sea"][0] + "-" + re.sub(r"[^a-z0-9]+", "-", r["name"].lower()).strip("-")
        else:
            r["code"] = r["sea"][0] + r["rl_code"]
    return out


def _key(code: str) -> str:
    return code.upper().replace(" ", "_")


def eea_codes(eunis_m_2022_xlsx: Path) -> list[dict]:
    """(publication code, working code, name) triples of the EEA crosswalk."""
    df = pd.read_excel(eunis_m_2022_xlsx, sheet_name="Benthic habitats", dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    out = {}
    for _, r in df[df["Red List code (for EEA publication)"].notna()].iterrows():
        pub, work = _split(r["Red List code (for EEA publication)"]), _split(r["Red List code"])
        names = _split(r["Red List name"])
        for i, p in enumerate(pub):
            out.setdefault(p, {"pub": p, "work": work[i] if i < len(work) else "",
                               "name": names[i] if i < len(names) else ""})
    return list(out.values())


def _assign(rows: list[dict], eea: list[dict]) -> None:
    """Give each Annex A row the EEA publication code (unique), matched by sea, working code and name."""
    used = set()
    for r in rows:
        prefix = r["sea"][0]
        if prefix == "BAL":
            cands = [e for e in eea if e["pub"] == r["code"]]
        else:
            cands = [e for e in eea if e["pub"].startswith(prefix) and _key(e["work"]) == _key(r["rl_code"])]
        cands = [e for e in cands if e["pub"] not in used]
        if not cands:                     # code misprinted or missing in Annex A: match by name
            sim = lambda e: difflib.SequenceMatcher(None, e["name"].lower(), r["name"].lower()).ratio()
            cands = [e for e in eea if e["pub"].startswith(prefix) and e["pub"] not in used and sim(e) > 0.85]
            if cands:
                r["matched_by_name"] = True
        if len(cands) > 1:
            cands.sort(key=lambda e: -difflib.SequenceMatcher(None, e["name"].lower(), r["name"].lower()).ratio())
        if cands:
            r["pub"] = cands[0]["pub"]
            used.add(r["pub"])


def habitats(sources: Path, eunis_m_2022_xlsx: Path | None = None) -> pd.DataFrame:
    rows_a = annex_a(sources)
    if eunis_m_2022_xlsx is not None and eunis_m_2022_xlsx.is_file():
        _assign(rows_a, eea_codes(eunis_m_2022_xlsx))
    rows = [{"system": "EU_REDLIST_2016", "code": p, "name": n, "level": 1, "parent_code": None, "realm": "marine",
             "group": "benthic", "description": None, "source": SRC + ", Annex A", "notes": "regional sea"}
            for p, n in SEAS.values()]
    seen = set()
    for r in rows_a:
        crit = lambda c: f" ({c})" if c and c != "-" else ""
        code = r.get("pub") or r["code"]
        notes = [f"EU28: {r['eu28']}{crit(r['crit28'])}", f"EU28+: {r['eu28p']}{crit(r['crit28p'])}",
                 f"code in Annex A: {r['rl_code']}" if r["rl_code"] != "-" else "no code in Annex A"]
        if not r.get("pub"):
            notes.append("no EEA publication code found; code built from Annex A")
        elif r.get("matched_by_name"):
            notes.append("EEA publication code matched by name (code differs in Annex A)")
        if code in seen:
            code += "-" + re.sub(r"[^a-z0-9]+", "-", r["name"].lower()).strip("-")[:40]
            notes.append("duplicate code in Annex A")
        seen.add(code)
        rows.append({"system": "EU_REDLIST_2016", "code": code, "name": r["name"], "level": 2,
                     "parent_code": r["sea"][0], "realm": "marine", "group": "benthic", "description": None,
                     "source": SRC + ", Annex A", "notes": "; ".join(notes)})
    df = pd.DataFrame(rows)
    df["level"] = df["level"].astype("Int64")
    return df[HABITATS_COLUMNS]


def _split(v) -> list[str]:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return []
    return [x.strip().strip(":").replace("\xa0", "").strip() for x in re.split(r";|\n", str(v))
            if x.strip().strip(":").replace("\xa0", "").strip()]


def crosswalk_eunis2022(eunis_m_2022_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(eunis_m_2022_xlsx, sheet_name="Benthic habitats", dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    rows = []
    for _, r in df[df["Red List code (for EEA publication)"].notna()].iterrows():
        codes = _split(r["Red List code (for EEA publication)"])
        rels = _split(r["Red List relationship"])
        for i, c in enumerate(codes):
            rel = rels[i] if i < len(rels) else (rels[0] if len(rels) == 1 else "unspecified")
            rows.append({"from_system": "EUNIS_M_2022", "from_code": str(r["Code"]).strip(),
                         "to_system": "EU_REDLIST_2016", "to_code": c, "relationship": rel, "source": SRC_EEA,
                         "notes": "" if len(rels) == len(codes) else
                         f"EEA file gives {len(rels)} relationship(s) for {len(codes)} Red List code(s)"})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()
