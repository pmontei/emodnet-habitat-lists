from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.build import EUNIS_M_2022_XLSX
from emodnet_habitat_lists.sources import redlist

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
pytestmark = pytest.mark.skipif(not (SOURCES / redlist.FOLDER).is_dir() or not pdftext.available(),
                                reason="Red List report or pdftotext not available")


def test_annex_a_totals():
    import collections
    rows = redlist.annex_a(SOURCES)
    assert len(rows) == 257
    by_sea = collections.Counter(r["sea"][0] for r in rows)
    assert by_sea == {"BAL": 61, "NEA": 86, "MED": 47, "BLS": 63}
    # report Table 3.1.1, EU28+ totals
    assert collections.Counter(r["eu28p"] for r in rows) == {"DD": 137, "LC": 47, "NT": 28, "VU": 25, "EN": 18,
                                                               "CR": 2}


def test_codes_and_crosswalk():
    x = SOURCES / EUNIS_M_2022_XLSX
    h = redlist.habitats(SOURCES, x)
    assert h.code.is_unique
    if x.is_file():
        assert {"NEAA5.67", "NEAA5.53A", "BLSA1.4C"} <= set(h.code)
        cw = redlist.crosswalk_eunis2022(x)
        assert set(cw.to_code) - set(h.code) == {"RLA2.5a", "RLA2.5b", "RLA2.5c", "RLA2.5d"}
