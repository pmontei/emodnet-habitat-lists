from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import iucn_get

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
pytestmark = pytest.mark.skipif(not (SOURCES / iucn_get.FOLDER).is_dir() or not pdftext.available(),
                                reason="GET 2.0 or pdftotext not available")


def test_levels():
    h = iucn_get.habitats(SOURCES)
    assert h.code.is_unique
    v20 = h[~h.notes.str.contains("v2.1")]
    assert v20.level.value_counts().to_dict() == {3: 108, 2: 25, 1: 10}
    assert set(h.parent_code.dropna()) <= set(h.code)
    r = h.set_index("code")
    assert r.loc["M3.5", "name"] == "Deepwater biogenic beds" and r.loc["M1.10", "level"] == 3
