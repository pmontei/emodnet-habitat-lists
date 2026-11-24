from pathlib import Path

import pytest

from emodnet_habitat_lists.build import EUNIS_M_2022_XLSX
from emodnet_habitat_lists.sources import eunis_eea

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
XLSX = SOURCES / EUNIS_M_2022_XLSX


@pytest.mark.skipif(not XLSX.is_file(), reason="EEA EUNIS marine 2022 file not available")
def test_m2022_2012():
    cw = eunis_eea.crosswalk_m2022_2012(XLSX)
    assert len(cw) > 2400
    assert set(cw.relationship) <= {"=", "<", ">", "#", "unspecified"}
    rel = {(a, b): r for a, b, r in zip(cw.from_code, cw.to_code, cw.relationship)}
    assert rel[("MA1", "A1")] == "=" and rel[("MH", "A7")] == "=" and rel[("MJ", "A8")] == "="
    assert ("MB4", "A5.4") in rel and ("ME2", "A6") in rel and ("MA223T", "A2.531J") in rel
    assert not cw.to_code.str.contains("Α|\\xa0").any()
