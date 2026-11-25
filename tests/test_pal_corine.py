from pathlib import Path

import pandas as pd
import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import pal_corine as pc

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
HAS_PAL = (SOURCES / pc.PAL_FOLDER).is_dir()


@pytest.mark.skipif(not HAS_PAL, reason="PAL source not available")
def test_pal():
    p = pc.pal_habitats(SOURCES)
    assert len(p) == 6228 and p.code.is_unique
    assert p.level.value_counts().to_dict() == {5: 2155, 6: 1711, 4: 1228, 7: 591, 3: 355, 8: 111, 2: 68, 1: 9}
    assert set(p.parent_code.dropna()) <= set(p.code)
    assert dict(zip(p.code, p.name))["11.34"] == "[Posidonia] beds"


@pytest.mark.skipif(not (HAS_PAL and (SOURCES / pc.CORINE_FOLDER).is_dir() and pdftext.available()),
                    reason="CORINE source not available")
def test_corine_chapters_1_2():
    c = pc.corine_habitats(SOURCES)
    assert len(c) == 325 and c.code.is_unique
    assert set(c.code.str[0]) == {"1", "2"}
    assert set(c.parent_code.dropna()) <= set(c.code)
    n = dict(zip(c.code, c.name))
    assert n["11.34"] == "Posidonia beds" and n["13.11"] == "Brackish water" and n["16.272"] == "Lycian juniper woods"
    assert n["15"] == "Salt marshes, salt steppes and gypsum scrubs"
    assert dict(zip(c.code, c.parent_code))["11.121"] == "11.12"
    assert not c.notes.str.contains("to check").any()


def test_pal_expressions():
    cw = pd.DataFrame([{"from_system": "ANNEX_I", "from_code": "2130", "to_system": "PAL_CLASS",
                        "to_code": "16.221 to 16.223", "relationship": "unspecified", "source": "", "notes": ""},
                       {"from_system": "ANNEX_I", "from_code": "1150", "to_system": "PAL_CLASS",
                        "to_code": "(22.12 or 22.15) x 22.44", "relationship": "unspecified", "source": "", "notes": ""}])
    out = pc.expand_pal_expressions(cw, {"16.221", "16.222", "16.223", "16.224", "22.12", "22.15", "22.44"})
    assert sorted(out[out.from_code == "2130"].to_code) == ["16.221", "16.222", "16.223"]
    assert sorted(out[out.from_code == "1150"].to_code) == ["22.12", "22.15", "22.44"]


@pytest.mark.skipif(not (PROCESSED / "crosswalks.csv").is_file(), reason="run ehl-build first")
def test_pal_corine_codes_resolve():
    c = pd.read_csv(PROCESSED / "crosswalks.csv", dtype=str)
    bad = c[c.notes.fillna("").str.contains(r"not found in (?:PAL_CLASS|CORINE)")]
    # 1997 PAL codes not in PHYSIS 2001, and CORINE 12.7 (a transposed code not printed in the manual)
    assert set(bad.to_code) <= {"42C51", "36.44", "44.A14", "61.15", "12.7"}
