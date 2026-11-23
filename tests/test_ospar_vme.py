from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import ices_vme, ospar

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"


def test_ospar_list():
    h = ospar.habitats()
    top = h[h.level == 1]
    assert len(top) == 18
    assert set(h.parent_code.dropna()) <= set(top.code)


@pytest.mark.skipif(not (SOURCES / ospar.FOLDER).is_dir() or not pdftext.available(),
                    reason="OSPAR sources or pdftotext not available")
def test_ospar_crosswalks():
    cw = ospar.crosswalks(SOURCES)
    e = cw[cw.to_system == "EUNIS_2012"]
    assert set(e[e.from_code == "zostera-beds"].to_code) == {"A2.611", "A5.533", "A5.545"}
    assert len(e[e.from_code == "kelp-forest"]) == 25
    assert set(cw[cw.from_code == "maerl-beds"].to_code) >= {"A5.51", "SS.SMp.Mrl", "habtype=Maerl beds"}
    # every OSPAR habitat with EMODnet data is linked to its habtype
    em = cw[cw.to_system == "EMODNET_OSPAR2025"]
    assert "?" not in set(em.from_code)
    assert len(em[~em.to_code.str.contains(r"\|")]) == 17  # Cymodocea meadows absent from the dataset


@pytest.mark.skipif(not (SOURCES / ices_vme.FOLDER).is_dir(), reason="VME sources not available")
def test_ices_vme():
    v = ices_vme.habitats(SOURCES)
    active = v[~v.notes.str.contains("deprecated")]
    assert len(active[active.level == 1]) == 10
    assert len(active[active.level == 2]) == 16
    assert set(v.parent_code.dropna()) <= set(v[v.level == 1].code)
