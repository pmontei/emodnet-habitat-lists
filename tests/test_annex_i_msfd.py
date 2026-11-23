from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.build import EUNIS_M_2022_XLSX
from emodnet_habitat_lists.sources import annex_i, msfd_bht

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
needs_annex = pytest.mark.skipif(not (SOURCES / annex_i.FOLDER).is_dir() or not pdftext.available(),
                                 reason="Habitats Directive sources or pdftotext not available")
needs_msfd = pytest.mark.skipif(not (SOURCES / msfd_bht.FOLDER).is_dir() or not pdftext.available(),
                                reason="MSFD sources or pdftotext not available")


@needs_annex
def test_annex_i_list():
    h = annex_i.habitats(SOURCES)
    types = h[h.level == 3]
    assert len(types) == 233                      # Annex I after the accession of Croatia
    assert len(h[h.level == 1]) == 9
    assert set(h.parent_code.dropna()) <= set(h.code)
    assert types.description.notna().all()        # every type found in the Interpretation Manual EUR28
    r = types.set_index("code")
    assert r.loc["1120", "name"] == "Posidonia beds (Posidonion oceanicae)"
    assert "priority" in r.loc["1120", "notes"] and "priority" not in r.loc["1170", "notes"]
    assert r.loc["1170", "description"].startswith("Reefs can be either biogenic concretions")
    assert set(types[types.realm == "marine"].code) == {
        "1110", "1120", "1130", "1140", "1150", "1160", "1170", "1180", "1610", "1620", "1650", "8330"}
    assert r.loc["4070", "parent_code"] == "4"    # group 4 has no sub-groups in the Directive


@needs_annex
def test_annex_i_manual_crosswalks():
    cw = annex_i.crosswalk_manual(SOURCES)
    e = cw[cw.to_system == "EUNIS_2012"]
    assert set(e.from_code) == {"1110", "1170", "1180"}
    assert set(e[e.from_code == "1110"].to_code) == {"A5.1", "A5.2", "A5.4", "A5.5"}
    assert set(e[e.from_code == "1180"].to_code) == {"A5.71"}
    pal = cw[cw.to_system == "PAL_CLASS"]
    assert set(pal[pal.from_code == "1110"].to_code) == {"11.125", "11.22", "11.31", "11.333"}
    assert pal[(pal.from_code == "93A0")].relationship.tolist() == ["partim"]


@needs_annex
def test_annex_i_eea_crosswalk():
    xlsx = SOURCES / EUNIS_M_2022_XLSX
    if not xlsx.is_file():
        pytest.skip("EUNIS marine 2022 file not available")
    cw = annex_i.crosswalk_eunis2022(xlsx)
    assert set(cw.relationship) <= {"=", "<", ">", "#", "unspecified"}
    assert set(cw[cw.from_code == "MA121"].to_code) == {"1160", "1170"}
    assert set(cw.to_code) <= set(annex_i.habitats(SOURCES).code)


@needs_msfd
def test_msfd_bht():
    h = msfd_bht.habitats(SOURCES)
    assert len(h) == 22
    cw = msfd_bht.crosswalk_eunis(SOURCES)
    assert set(cw[cw.from_code == "abyssal"].to_code) == {f"MG{i}" for i in range(1, 7)}
    assert cw[cw.from_code == "infralittoral-sand"].relationship.tolist() == ["="]
    # every EUNIS marine level-2 benthic code (MA1 ... MG6) is covered exactly once
    assert len(cw) == len(set(cw.to_code)) == 42
