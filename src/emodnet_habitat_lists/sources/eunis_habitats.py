"""EUNIS habitats from the ``{eunis.habitats}`` R package.

``{eunis.habitats}`` (Magno, Monteiro & Bentes; CRAN) ships a single tidy table,
``eunis_habitats``, with four EUNIS classifications: EUNIS_2012, EUNIS_M_2019,
EUNIS_M_2022 and EUNIS_T_2021. We read its ``.rda`` file directly with ``pyreadr`` so
that the Python tables stay identical to, and compatible with, the R package.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd

from ..schema import HABITATS_COLUMNS

RDA_URL = (
    "https://raw.githubusercontent.com/ramiromagno/eunis.habitats/main/data/eunis_habitats.rda"
)
SOURCE_LABEL = "eunis.habitats R package (ramiromagno/eunis.habitats), data/eunis_habitats.rda"


def fetch_rda(dest: Path, url: str = RDA_URL, overwrite: bool = False) -> Path:
    """Download ``eunis_habitats.rda`` to ``dest`` (cached unless ``overwrite``)."""
    dest = Path(dest)
    if dest.exists() and not overwrite:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    return dest


def _parent_codes(df: pd.DataFrame) -> list[str | None]:
    """Parent of each habitat: the longest prefix of its code that exists in the same
    system at level - 1. Works for dotted (EUNIS 2012: ``A1.11`` -> ``A1.1``) and undotted
    codes (EUNIS 2019/2022: ``MA121`` -> ``MA12``; ``MA1`` -> ``M``; terrestrial 2021)."""
    index = {(s, c): lvl for s, c, lvl in zip(df["system"], df["code"], df["level"])}
    parents: list[str | None] = []
    for s, c, lvl in zip(df["system"], df["code"], df["level"]):
        parent = None
        if isinstance(c, str) and pd.notna(lvl) and lvl > 1:
            for k in range(len(c) - 1, 0, -1):
                cand = c[:k].rstrip(".")
                if index.get((s, cand)) == lvl - 1:
                    parent = cand
                    break
        parents.append(parent)
    return parents


def load(rda_path: Path) -> pd.DataFrame:
    """Return the EUNIS habitats in the ``habitats`` schema."""
    import pyreadr

    raw = pyreadr.read_r(str(rda_path))["eunis_habitats"]
    df = pd.DataFrame(
        {
            "system": raw["classification"],
            "code": raw["code"].str.strip(),
            "name": raw["name"],
            "level": pd.to_numeric(raw["level"], errors="coerce").astype("Int64"),
            "realm": raw["section"],
            "group": raw["group"],
            "description": raw["description"],
            "source": SOURCE_LABEL,
        }
    )
    # the upstream table contains 90 empty rows (no code, no name; 89 in the terrestrial
    # "man-made" group of EUNIS_T_2021 and 1 in EUNIS_2012); they carry no information
    df = df[df["code"].notna() & (df["code"] != "")].reset_index(drop=True)
    df["parent_code"] = _parent_codes(df)
    return df[HABITATS_COLUMNS]
