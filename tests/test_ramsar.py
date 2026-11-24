from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import ramsar

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
pytestmark = pytest.mark.skipif(not list((SOURCES / ramsar.FOLDER).glob(ramsar.CROSSWALK_GLOB))
                                if (SOURCES / ramsar.FOLDER).is_dir() else True,
                                reason="Ramsar crosswalk not available")


def test_type_lists():
    assert len(ramsar.MARINE_COASTAL) == 12 and len(ramsar.INLAND) == 20 and len(ramsar.HUMAN_MADE) == 10


@pytest.mark.skipif(not pdftext.available(), reason="pdftotext not available")
def test_get_crosswalk():
    cw = ramsar.crosswalk_get(SOURCES)
    allc = set(ramsar.MARINE_COASTAL + ramsar.INLAND + ramsar.HUMAN_MADE)
    assert allc - set(cw.from_code) == {"A", "B", "C", "Zk(a)", "Zk(c)"}
    g = cw.groupby("from_code").to_code.apply(set)
    assert g["I"] == {"MFT1.1", "MFT1.2"} and g["K"] == {"MFT1.1", "F2.1", "F2.2"} and g["J"] == {"FM1.3"}
