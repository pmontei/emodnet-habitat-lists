from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.schema import HABITATS_COLUMNS
from emodnet_habitat_lists.sources import barcelona as bc

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
pytestmark = pytest.mark.skipif(
    not (SOURCES / bc.FOLDER).is_dir() or not pdftext.available(),
    reason="Barcelona Convention source files or pdftotext not available",
)


@pytest.fixture(scope="module")
def bc2019():
    return bc.load_2019(SOURCES)


@pytest.fixture(scope="module")
def bc2006():
    return bc.load_2006(SOURCES)


def test_counts(bc2019, bc2006):
    cl, rl = bc2019
    assert len(cl) == 394
    assert len(rl) == 267
    assert len(bc2006) == 189
    assert list(cl.columns) == HABITATS_COLUMNS


def test_reference_list_is_subset(bc2019):
    cl, rl = bc2019
    assert set(rl["code"]) <= set(cl["code"])


@pytest.mark.parametrize("df_idx", [0, 1])
def test_hierarchy_complete(bc2019, df_idx):
    df = bc2019[df_idx]
    assert not df["code"].duplicated().any()
    codes = set(df["code"])
    assert df["parent_code"].dropna().isin(codes).all()


@pytest.mark.parametrize(
    "code,level,parent",
    [
        ("MA1.5", 3, None),
        ("MA1.51", 4, "MA1.5"),
        ("MA1.511", 5, "MA1.51"),
        ("MA1.51a", 5, "MA1.51"),
        ("MB1.511a", 6, "MB1.51a"),
        ("MC2.51A", 5, "MC2.51"),
        ("MC1.51Ab", 6, "MC1.51b"),
        ("ME2.5", 3, None),       # printed without space before the name
        ("MD3.512", 5, "MD3.51"),  # erratum: printed as ME2.512
    ],
)
def test_codes(bc2019, code, level, parent):
    row = bc2019[0].set_index("code").loc[code]
    assert row["level"] == level
    assert (row["parent_code"] if isinstance(row["parent_code"], str) else None) == parent


def test_classification_matches_sparac_publication(bc2019):
    diff = bc.check_against_sparac(bc2019[0], SOURCES)
    assert diff == {"only_in_decision": [], "only_in_sparac": []}


def test_2006_hierarchy(bc2006):
    assert bc2006["parent_code"].dropna().isin(set(bc2006["code"])).all()
    assert "IV.2.2.10" in set(bc2006["code"])  # erratum: printed as V.2.2.10


def test_manual_crosswalk():
    cw = bc.crosswalk_manual(SOURCES)
    assert {"EUNIS_M_2019", "EUNIS_2012", "ANNEX_I"} <= set(cw["to_system"])
    # sheet MA1.54: "EUNIS 2019: MA154 / EUNIS 2007: A1.14 (partim), ... / EC: 1170 (partim)"
    r = cw[(cw.from_code == "MA1.54") & (cw.to_system == "ANNEX_I")]
    assert set(zip(r.to_code, r.relationship)) == {("1170", "partim")}
    assert "MB252" in set(cw[(cw.from_code == "MB2.54") & (cw.to_system == "EUNIS_M_2019")].to_code)
