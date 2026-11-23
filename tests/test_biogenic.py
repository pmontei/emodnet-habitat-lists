from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import biogenic

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
needs = pytest.mark.skipif(not (SOURCES / biogenic.FOLDER).is_dir() or not pdftext.available(),
                           reason="biogenic substrate report or pdftotext not available")


def test_typology():
    h = biogenic.habitats()
    assert h.code.is_unique and len(h[h.level == 1]) == 1
    assert set(h.parent_code.dropna()) <= set(h.code)
    assert len(h[h.level == 2]) == 10


@needs
def test_typology_names_in_report():
    text = biogenic._norm(biogenic._text(SOURCES))
    assert [n for n, *_ in biogenic.TYPOLOGY if biogenic._norm(n) not in text] == []


@needs
def test_appendix1():
    cw = biogenic.crosswalk_appendix1(SOURCES)
    assert set(cw.to_code) <= set(biogenic.habitats().code)
    e = cw[(cw.from_system == "EUNIS_2012") & cw.notes.str.contains("Mediterranean")]
    assert dict(zip(e.from_code, e.to_code))["A5.535"] == "posidonia-oceanica-meadows"
    hub = cw[cw.from_system == "HELCOM_HUB"]
    assert dict(zip(hub.from_code, hub.to_code))["AA.H1E3"] == "dominated-by-valve-snails"
    assert len(hub) == 38


@needs
def test_appendix2():
    cw = biogenic.crosswalk_appendix2(SOURCES)
    assert len(cw) == 101
    assert set(cw.from_code) <= set(biogenic.habitats().code)
    corr = cw[cw.notes.str.contains("report correction")]
    assert set(corr.to_code) == {"MB2211", "MB2212", "MB2224", "MC223", "MC2237", "MC2238", "MD22"}
    assert not cw.notes.str.contains("name in report: ;").any()
