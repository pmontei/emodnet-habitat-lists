from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import annex_i, bern

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
pytestmark = pytest.mark.skipif(not (SOURCES / bern.FOLDER).is_dir() or not pdftext.available(),
                                reason="Bern Convention sources or pdftotext not available")

JNCC_EMERALD = {"A1.11", "A1.22", "A1.44", "A2.2", "A2.3", "A2.4", "A2.5", "A2.61", "A2.72", "A3", "A4", "A5",
                "A6.1", "A6.61", "A6.911"}


def test_list():
    h = bern.habitats(SOURCES)
    assert h.code.is_unique and len(h[h.level == 2]) == 213
    marine = set(h[(h.level == 2) & h.code.str.startswith("A")].code)
    assert JNCC_EMERALD <= marine and len(marine) == 17
    assert h.set_index("code").loc["A6.1", "name"].endswith("(but excluding A6.12 Deep sea artificial hard substrata)")
    assert h[h.level == 2].description.isna().sum() <= 1


def test_annex_i():
    cw = bern.crosswalk_annex_i(SOURCES, set(annex_i.habitats(SOURCES).code)
                                if (SOURCES / annex_i.FOLDER).is_dir() else None)
    rel = {(a, b): r for a, b, r in zip(cw.from_code, cw.to_code, cw.relationship)}
    assert rel[("A1.11", "1170")] == "<"
    assert rel[("A6.61", "1170")] == "<"
    assert rel[("A2.2", "1140")] == "occurs within"
    assert rel[("X01", "1130")] == "unspecified"
