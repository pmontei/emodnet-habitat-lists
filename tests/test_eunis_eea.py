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


EEA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "eunis_eea"
F19 = EEA_DIR / f"{eunis_eea.FILES['EUNIS_M_2019']}.xlsx"
F22 = EEA_DIR / f"{eunis_eea.FILES['EUNIS_M_2022']}.xlsx"
FT = EEA_DIR / f"{eunis_eea.FILES['EUNIS_T_2021']}.xlsx"


@pytest.mark.skipif(not (F19.is_file() and FT.is_file()), reason="EEA 2019 / terrestrial files not fetched")
def test_m2019_and_t2021_to_2012():
    m19 = eunis_eea.crosswalk_to_2012(F19, "EUNIS_M_2019")
    assert len(m19) > 2300 and set(m19.from_system) == {"EUNIS_M_2019"}
    t21 = eunis_eea.crosswalk_to_2012(FT, "EUNIS_T_2021")
    rel = {(a, b): r for a, b, r in zip(t21.from_code, t21.to_code, t21.relationship)}
    # U11 lists four 2012 codes separated by ';' and relationships separated by ','
    assert all(rel[("U11", c)] == ">" for c in ("H1.1", "H1.2", "H1.3", "H1.4"))
    assert not t21.from_code.str.startswith("V").any()          # Man-made sheet skipped


@pytest.mark.skipif(not (F19.is_file() and F22.is_file()), reason="EEA 2019 / 2022 files not fetched")
def test_m2019_m2022():
    cw, new = eunis_eea.crosswalk_m2019_m2022(F19, F22)
    assert sorted(new) == ["MA223T", "MB2223", "MC128"]          # the 3 additions in the 2022 'Read me'
    assert len(cw) == 1939 and cw.from_code.is_unique and set(cw.relationship) == {"="}
    m = dict(zip(cw.from_code, cw.to_code))
    # re-used codes: matched by name, not by code
    assert m["MC1222"] == "MC2231" and m["MC1223"] == "MC1222" and m["MC128"] == "MC223"
    assert m["MC2214"] == "MC2232" and m["MC12251"] == "MC12241" and m["MA432"] == "MA432"
    assert "ATL -> ARC" in cw.set_index("from_code").notes["ME311"]
