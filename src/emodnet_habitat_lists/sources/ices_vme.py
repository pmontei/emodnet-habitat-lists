"""ICES Vulnerable Marine Ecosystem (VME) habitat types and subtypes.

System produced
---------------
``ICES_VME``
    ICES vocabulary code types ``HabitatType`` (level 1, https://vocab.ices.dk/?ref=1410) and
    ``HabitatSubtype`` (level 2, https://vocab.ices.dk/?ref=1411), as used in the ICES VME
    database (fields VME_HabitatType / VME_HabitatSubtype). Deprecated codes are kept and flagged.

ICES does not publish the habitat type of each subtype: ``parent_code`` comes from the
``parent_type`` column of the transcription, inferred from codes and names (see notes).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..schema import HABITATS_COLUMNS

FOLDER = "5.VME (FAO  ICES)"
VOCAB_CSV = "04_2023_ICES_vocab_VME-HabitatType-Subtype.csv"
SRC = "ICES Vocabulary Server (RECO), code types HabitatType (ref 1410) and HabitatSubtype (ref 1411), last modified 2023-09-21"


def habitats(sources: Path) -> pd.DataFrame:
    v = pd.read_csv(sources / FOLDER / VOCAB_CSV, dtype=str, keep_default_na=False)
    rows = []
    for r in v.itertuples():
        is_sub = r.code_type == "HabitatSubtype"
        notes = []
        if r.deprecated == "True":
            notes.append("deprecated in the ICES vocabulary")
        if is_sub:
            notes.append("parent habitat type inferred (not published by ICES)")
        rows.append({
            "system": "ICES_VME", "code": r.code, "name": r.description,
            "level": 2 if is_sub else 1, "parent_code": (r.parent_type or None) if is_sub else None,
            "realm": "marine", "group": "deep-sea", "description": None,
            "source": f"{SRC}; created {r.created}, modified {r.modified}", "notes": "; ".join(notes),
        })
    df = pd.DataFrame(rows)
    df["level"] = df["level"].astype("Int64")
    return df[HABITATS_COLUMNS]
