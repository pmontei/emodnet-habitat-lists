"""Members of the composite-product lists that are derived (proposed) rather than published.

EMODNET_BIOGENIC in EUNIS 2022 (D3.10)
--------------------------------------
Proposal of the EUNIS 2022 habitats that make up the biogenic substrate product, obtained by
converting the list published in EUNIS 2019 (D3.06, Appendix 2: ``EMODNET_BIOGENIC_2021 ->
EUNIS_M_2019``, ``maps to (with biological zone)``) with the ``EUNIS_M_2019 -> EUNIS_M_2022``
crosswalk (matched by name, see ``sources/eunis_eea.py``).

* Codes present in EUNIS 2019 are converted with that crosswalk.
* The report's "unofficial corrections" (codes not in EUNIS 2019) are resolved against
  EUNIS 2022 in ``REPORT_CORRECTIONS`` (adopted, recoded, or a probable equivalent to review).
* For each code the EUNIS 2022 sub-tree is compared with the 2019 sub-tree: units that entered
  or left the sub-tree in 2022 (e.g. *Sabellaria spinulosa* encrusted rock moved from the
  biogenic ``MC221`` to rock ``MC128``) are returned as review reasons, which end up in the
  ``notes`` of the ``list_members`` rows ("TO REVIEW: ...").

All rows are ``proposed`` members until reviewed by WP3.
"""

from __future__ import annotations

import pandas as pd

from .schema import CROSSWALKS_COLUMNS

REL_APP2 = "maps to (with biological zone)"

# report code (not in EUNIS 2019) -> (EUNIS 2022 code, include, why)
REPORT_CORRECTIONS = {
    "MC223": ("MC223", "yes", "report correction adopted in EUNIS 2022 (same code and name)"),
    "MC2237": ("MC2235", "yes", "report correction adopted in EUNIS 2022 with code MC2235 (same name)"),
    "MC2238": ("MC2236", "yes", "report correction adopted in EUNIS 2022 with code MC2236 (same name)"),
    "MB2224": ("MB2223", "review",
               "report proposed MB2224 'Mytilus edulis beds on Atlantic infralittoral sediment'; EUNIS 2022 added "
               "MB2223 'Mussel beds on Atlantic infralittoral sediment' (probable equivalent, broader name)"),
}


def _descendants(habitats: pd.DataFrame, system: str) -> dict[str, set[str]]:
    h = habitats[habitats.system == system]
    children: dict[str, list[str]] = {}
    for c, p in zip(h.code, h.parent_code):
        if isinstance(p, str) and p:
            children.setdefault(p, []).append(c)
    out: dict[str, set[str]] = {}

    def walk(c: str) -> set[str]:
        if c not in out:
            s: set[str] = set()
            for k in children.get(c, []):
                s |= {k} | walk(k)
            out[c] = s
        return out[c]

    for c in h.code:
        walk(c)
    return out


def biogenic_eunis2022(habitats: pd.DataFrame, crosswalks: pd.DataFrame
                       ) -> tuple[dict[tuple[str, str], str], pd.DataFrame]:
    """Return ({("EUNIS_M_2022", code): reason to review}, rows EMODNET_BIOGENIC_2021 -> EUNIS_M_2022)."""
    app2 = crosswalks[(crosswalks.from_system == "EMODNET_BIOGENIC_2021") &
                      (crosswalks.to_system == "EUNIS_M_2019")]
    m = crosswalks[(crosswalks.from_system == "EUNIS_M_2019") & (crosswalks.to_system == "EUNIS_M_2022")]
    to22 = dict(zip(m.from_code, m.to_code))
    to19 = dict(zip(m.to_code, m.from_code))
    d19, d22 = _descendants(habitats, "EUNIS_M_2019"), _descendants(habitats, "EUNIS_M_2022")

    cw_rows, per_code = [], {}
    for _, r in app2.iterrows():
        c19 = r.to_code
        if c19 in to22:
            c22, include, why = to22[c19], "yes", f"EUNIS 2019 {c19} = EUNIS 2022 {to22[c19]}"
        elif c19 in REPORT_CORRECTIONS:
            c22, include, why = REPORT_CORRECTIONS[c19]
            why = f"{c19}: {why}"
        else:
            raise ValueError(f"Appendix 2 code {c19} not resolved in EUNIS 2022")
        region_zone = "; ".join(x for x in str(r.notes).split("; ") if x.startswith(("region:", "biological zone:")))
        cw_rows.append({"from_system": "EMODNET_BIOGENIC_2021", "from_code": r.from_code,
                        "to_system": "EUNIS_M_2022", "to_code": c22, "relationship": REL_APP2,
                        "source": "D3.06 Appendix 2 converted with EUNIS_M_2019 -> EUNIS_M_2022",
                        "notes": f"{region_zone}; {why}"})
        e = per_code.setdefault(c22, {"types": [], "why": set(), "include": "yes", "region_zone": set()})
        e["types"].append(r.from_code)
        e["why"].add(why)
        e["region_zone"].add(region_zone)
        if include == "review":
            e["include"] = "review"

    review: dict[tuple[str, str], str] = {}
    for c22, e in per_code.items():
        reasons = [w for w in sorted(e["why"]) if e["include"] == "review" and "probable equivalent" in w]
        c19 = to19.get(c22)
        if c19 is not None:
            sub22 = d22.get(c22, set())
            sub19_as22 = {to22[x] for x in d19.get(c19, set()) if x in to22}
            gained, lost = sorted(sub22 - sub19_as22), sorted(sub19_as22 - sub22)
            if gained:
                reasons.append("sub-tree changed in 2022, entered: " +
                               ", ".join(f"{x} ({'new in 2022' if x not in to19 else 'EUNIS 2019 ' + to19[x]})"
                                         for x in gained))
            if lost:
                reasons.append("sub-tree changed in 2022, left: " +
                               ", ".join(f"{x} (EUNIS 2019 {to19.get(x, '?')})" for x in lost))
        if reasons:
            review[("EUNIS_M_2022", c22)] = "; ".join(reasons)
    return review, pd.DataFrame(cw_rows, columns=CROSSWALKS_COLUMNS).drop_duplicates()
