from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import carib

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
pytestmark = pytest.mark.skipif(not list((SOURCES / carib.FOLDER).glob(carib.TYPOLOGY_GLOB))
                                if (SOURCES / carib.FOLDER).is_dir() else True or not pdftext.available(),
                                reason="Martinique typology or pdftotext not available")


def test_tree():
    h = carib.habitats(SOURCES)
    assert h.code.is_unique
    assert h.level.value_counts().to_dict() == {5: 118, 4: 68, 3: 39, 2: 14, 1: 6}
    assert set(h.parent_code.dropna()) <= set(h.code)
    r = h.set_index("code")
    assert r.loc["C2-5", "name"] == "Platiers de récif frangeant ou de massif corallien"
    assert r.loc["A1-31.1", "name"].endswith("faune associée du supralittoral")
    assert "C4-42" in r.loc["C4-42.3", "notes"]


def test_aphn():
    cw = carib.crosswalk_aphn(SOURCES)
    h = carib.habitats(SOURCES)
    assert set(cw.from_code) <= set(h.code)
    assert set(h[h.level == 5].code) - set(cw.from_code) == {"C4-23.2", "C4-34.8"}
    assert set(cw[cw.from_code == "D1-11.1"].to_code) == {"A11.B"}
