"""Marine Habitat Classification for Britain and Ireland (JNCC), version 22.04, and the JNCC
marine habitat correlation tables (version 2026.02).

System produced
---------------
``UK_MHC_2204``
    All units of the "Full biotope list" (broad habitat, habitat complex, biotope complex,
    biotope, sub-biotope), with the JNCC level (2 to 6). ``parent_code`` is the longest code of
    the list that is a dot-prefix of the code.

``UK_MHC_1503``, ``UK_MNCR_0405``, ``UK_MHC_9706`` (former versions)
    Units named in the correlation tables (columns "JNCCvNNNN Codes / Names / Levels"), i.e.
    every former unit that JNCC correlates with v22.04. Checked against the published counts:
    v04.05 474 units (introduction: 5 + 24 + 75 + 370, complete); v15.03 688 units = v04.05 +
    214 of the 216 units of the deep-sea section, the 2 missing ones (``M``, ``M.AtMB.Bi``) are
    added from JNCC Report 530, Appendix 2 (complete); v97.06 322 of the 364 types of JNCC Report
    229, Table 2.4 (7 + 21 + 60 + 196 + 80): the ~40 types that JNCC does not correlate (mostly
    littoral: lichens, rockpools, overhangs) are not loaded.

Crosswalks produced (sheet "Correlation Data")
-----------------------------------------------
``UK_MHC_2204 ->`` ``UK_MHC_1503``, ``UK_MNCR_0405``, ``UK_MHC_9706``, ``EUNIS_M_2022``,
``EUNIS_2012`` (JNCC "EUNIS 2007"), ``OSPAR_TD_2021``, ``ANNEX_I``, ``MSFD_BHT``, ``ICES_VME``,
``EMERALD`` (Bern Convention Res. 4), ``GOOS_EOV``, ``IUCN_GET``, and the UK lists ``UK_HPI``,
``UK_MCZ_FOCI``, ``UK_PMF``, ``UK_MCZ_BSH``.

JNCC relationship types are mapped to the repository vocabulary: "Is the same as" ``=``,
"Contains" ``>``, "Is contained within" ``<``, "Partially overlaps with" ``#``.

Lists that JNCC gives by name only are coded as follows: OSPAR and ICES VME names are matched to
the repository codes (``kelp-forest``, ``CG`` ...); MSFD broad habitat types use the same slug as
``MSFD_BHT``; the other name-only lists (GOOS EOV, UK lists) use a slug of the name.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS
from .goos_eov import code_for as eov_code
from .msfd_bht import slug

FOLDER = "8.Marine Habitat Classification for Britain and Ireland"
BIOTOPE_LIST_GLOB = "01_2022_JNCC_MHC-v22-04_*.xlsx"
CORRELATION_GLOB = "02_2026_JNCC_*correlation*.xls*"
DEEP_SEA_GLOBS = ("13_*Report-530-Appendix2*.xlsx", "JNCC-Report-530-appendix2*.xlsx")
SRC_DEEP = ("Parry, M.E.V. et al., 2015. A Deep-sea Section for the Marine Habitat Classification of Britain and "
            "Ireland. JNCC Report No. 530, Appendix 2 (deep-sea classification structure, rev. 10/02/2020)")
OLD_VERSIONS = {"JNCCv1503": "UK_MHC_1503", "JNCCv0405": "UK_MNCR_0405", "JNCCv9706": "UK_MHC_9706"}
SRC_LIST = "JNCC, 2022. Marine Habitat Classification for Britain and Ireland v22.04, full biotope list"
SRC_CORR = "JNCC, 2026. Marine habitat correlation tables v2026.02, sheet 'Correlation Data'"

RELATIONSHIPS = {"Is the same as": "=", "Contains": ">", "Is contained within": "<", "Partially overlaps with": "#"}

# JNCC column prefix -> (system, column holding the code, how to code it)
TARGETS = {
    "JNCCv1503": ("UK_MHC_1503", "Codes", "code"),
    "JNCCv0405": ("UK_MNCR_0405", "Codes", "code"),
    "JNCCv9706": ("UK_MHC_9706", "Codes", "code"),
    "EUNIS2022": ("EUNIS_M_2022", "Codes", "code"),
    "EUNIS2007": ("EUNIS_2012", "Codes", "code"),
    "OSPAR": ("OSPAR_TD_2021", "Names", "ospar"),
    "Annex1": ("ANNEX_I", "Codes", "code"),
    "HPI": ("UK_HPI", "Names", "slug"),
    "MCZFOCI": ("UK_MCZ_FOCI", "Names", "slug"),
    "PMF": ("UK_PMF", "Names", "slug"),
    "MCZBSH": ("UK_MCZ_BSH", "Names", "slug"),
    "MSFDBroadHabitat": ("MSFD_BHT", "Names", "slug"),
    "Emerald Habitat": ("EMERALD", "Codes", "code"),
    "GOOSEOV": ("GOOS_EOV", "Names", "eov"),
    "VME": ("ICES_VME", "Names", "vme"),
    "GET": ("IUCN_GET", "Codes", "code"),
}

# names used by JNCC that differ from the repository names
OSPAR_ALIASES = {
    "kelp forest": "kelp-forest",
    "seapen and burrowing megafauna communities": "sea-pen-burrowing-megafauna",
    "modiolus modiolus horse mussel beds": "modiolus-modiolus-beds",
}
VME_ALIASES = {
    "seapen fields": "SF",
    "lophelia pertusa /madrepora oculata reef": "LMR",
    "solenosmilia variabilis reef": "SVR",   # ICES vocabulary prints 'variablis'
}


def _one(folder: Path, pattern: str) -> Path:
    files = sorted(folder.glob(pattern))
    if not files:
        raise FileNotFoundError(f"{folder}/{pattern}")
    return files[0]


def _split(v) -> list[str]:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return []
    return [x.strip() for x in str(v).replace("_x000D_", "").split(";")]


def habitats(sources: Path) -> pd.DataFrame:
    df = pd.read_excel(_one(sources / FOLDER, BIOTOPE_LIST_GLOB), sheet_name=0, dtype=str)
    code_cols = [c for c in df.columns if c.endswith("Code")]
    rows = []
    for _, r in df.iterrows():
        code = next((str(r[c]).strip() for c in code_cols if pd.notna(r[c]) and str(r[c]).strip()), None)
        if not code:
            continue
        rows.append({"system": "UK_MHC_2204", "code": code, "name": str(r["Title"]).strip(),
                     "level": int(r["Level"]), "parent_code": None, "realm": "marine", "group": "benthic",
                     "description": None, "source": SRC_LIST, "notes": ""})
    codes = {x["code"] for x in rows}
    for x in rows:
        parts = x["code"].split(".")
        x["parent_code"] = next((".".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)
                                 if ".".join(parts[:i]) in codes), None)
    out = pd.DataFrame(rows)
    out["level"] = out["level"].astype("Int64")
    return out[HABITATS_COLUMNS]


def _parents(rows: list[dict]) -> None:
    codes = {x["code"] for x in rows}
    for x in rows:
        parts = x["code"].split(".")
        x["parent_code"] = next((".".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)
                                 if ".".join(parts[:i]) in codes), None)


def old_versions_habitats(sources: Path) -> pd.DataFrame:
    """Former versions (15.03, 04.05, 97.06) from the correlation tables (see module docstring)."""
    df = pd.read_excel(_one(sources / FOLDER, CORRELATION_GLOB), sheet_name="Correlation Data", dtype=str)
    out = []
    for prefix, system in OLD_VERSIONS.items():
        seen: dict[str, dict] = {}
        for _, r in df.iterrows():
            codes, names, levels = (_split(r.get(f"{prefix} {c}")) for c in ("Codes", "Names", "Levels"))
            if not (len(codes) == len(names) == len(levels)):
                raise ValueError(f"{prefix}: codes, names and levels not aligned for {r['JNCCv2204 Code']}")
            for c, n, lv in zip(codes, names, levels):
                if c and c not in seen:
                    seen[c] = {"system": system, "code": c, "name": n, "level": int(lv), "parent_code": None,
                               "realm": "marine", "group": "benthic", "description": None,
                               "source": SRC_CORR + f", columns '{prefix} Codes / Names / Levels'", "notes": ""}
        rows = list(seen.values())
        if system == "UK_MHC_1503":
            deep = next((f for g in DEEP_SEA_GLOBS for f in sorted((sources / FOLDER).glob(g))), None)
            if deep is not None:
                a = pd.read_excel(deep, sheet_name=0, dtype=str)
                a.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in a.columns]
                for lv in range(1, 6):
                    for c, n in zip(a[f"Level {lv} Code"], a[f"Level {lv} Name"]):
                        if isinstance(c, str) and c.strip() and c.strip() not in seen:
                            seen[c.strip()] = {"system": system, "code": c.strip(), "name": str(n).strip(),
                                               "level": lv, "parent_code": None, "realm": "marine",
                                               "group": "benthic", "description": None, "source": SRC_DEEP,
                                               "notes": "not in the correlation tables; from the deep-sea "
                                                        "section (Report 530, Appendix 2)"}
                rows = list(seen.values())
        _parents(rows)
        out += rows
    o = pd.DataFrame(out, columns=HABITATS_COLUMNS)
    o["level"] = o["level"].astype("Int64")
    return o


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def crosswalks(sources: Path, ospar_habitats: pd.DataFrame | None = None,
               vme_habitats: pd.DataFrame | None = None) -> pd.DataFrame:
    """``ospar_habitats`` / ``vme_habitats``: repository tables used to code OSPAR and VME names."""
    ospar = {_norm(n): c for c, n in zip(ospar_habitats.code, ospar_habitats.name)} if ospar_habitats is not None else {}
    ospar |= {_norm(k): v for k, v in OSPAR_ALIASES.items()}
    vme = {_norm(n): c for c, n in zip(vme_habitats.code, vme_habitats.name)} if vme_habitats is not None else {}
    vme |= {_norm(k): v for k, v in VME_ALIASES.items()}

    df = pd.read_excel(_one(sources / FOLDER, CORRELATION_GLOB), sheet_name="Correlation Data", dtype=str)
    rows = []
    for _, r in df.iterrows():
        src_code = str(r["JNCCv2204 Code"]).strip()
        for prefix, (system, col, how) in TARGETS.items():
            rels = _split(r.get(f"{prefix} Relationships"))
            vals = _split(r.get(f"{prefix} {col}"))
            for i, v in enumerate(vals):
                if not v:
                    continue
                rel_raw = rels[i] if i < len(rels) else (rels[0] if len(rels) == 1 else "")
                notes = []
                if how == "code":
                    code = v
                elif how == "eov":
                    code = eov_code(v) or slug(v)
                    notes.append(f"JNCC name: {v}")
                elif how == "slug":
                    code = slug(v)
                    notes.append(f"JNCC name: {v}")
                else:
                    table = ospar if how == "ospar" else vme
                    code = table.get(_norm(v))
                    if code is None:
                        code = slug(v)
                        notes.append(f"JNCC name '{v}' not matched to a repository code")
                    else:
                        notes.append(f"JNCC name: {v}")
                if rel_raw and rel_raw not in RELATIONSHIPS:
                    notes.append(f"JNCC relationship: {rel_raw}")
                rows.append({"from_system": "UK_MHC_2204", "from_code": src_code, "to_system": system,
                             "to_code": code, "relationship": RELATIONSHIPS.get(rel_raw, "unspecified"),
                             "source": SRC_CORR + f", columns '{prefix} ...'", "notes": "; ".join(notes)})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()
