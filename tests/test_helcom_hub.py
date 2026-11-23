from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import helcom_hub as hh

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
pytestmark = pytest.mark.skipif(not (SOURCES / hh.FOLDER).is_dir() or not pdftext.available(),
                                reason="HELCOM HUB sources or pdftotext not available")


@pytest.fixture(scope="module")
def hub():
    return hh.habitats(SOURCES)


def test_annex1_and_complexes(hub):
    counts = hub["group"].value_counts().to_dict()
    assert counts["biotope/habitat"] == 328  # 207 photic + 115 aphotic + 1 sea ice + 5 pelagic
    assert counts["biotope complex"] == 10


def test_hierarchy(hub):
    units = hub[hub.group != "biotope complex"]
    assert not units["code"].duplicated().any()
    assert units["parent_code"].dropna().isin(set(units["code"])).all()


def test_red_list(hub):
    assert hub[hub.group != "higher level"]["notes"].str.contains("HELCOM Red List 2013").all()
    notes = hub.set_index("code")["notes"]
    assert notes["AB.H1I2"].startswith("HELCOM Red List 2013: EN")  # Haploops
    assert notes["1130"].startswith("HELCOM Red List 2013: CR")      # Estuaries
    assert "coded AB.H3M6 in BSEP 138" in notes["AB.H3M5"]


def test_fact_sheet_crosswalk():
    cw = hh.crosswalk_fact_sheets(SOURCES)
    r = cw[(cw.from_code == "AB.H3M5") & (cw.to_system == "EUNIS_2012")]
    assert set(r.to_code) == {"A5.378"}
