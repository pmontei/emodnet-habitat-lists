from pathlib import Path

import pytest

from emodnet_habitat_lists.schema import HABITATS_COLUMNS
from emodnet_habitat_lists.sources import eunis_habitats

RDA = Path(__file__).resolve().parents[1] / "data" / "raw" / "eunis_habitats.rda"


@pytest.fixture(scope="module")
def habitats():
    eunis_habitats.fetch_rda(RDA)
    return eunis_habitats.load(RDA)


def test_columns(habitats):
    assert list(habitats.columns) == HABITATS_COLUMNS


def test_systems_and_counts(habitats):
    counts = habitats["system"].value_counts().to_dict()
    assert counts["EUNIS_M_2022"] == 1942
    assert set(counts) == {"EUNIS_2012", "EUNIS_M_2019", "EUNIS_M_2022", "EUNIS_T_2021"}


@pytest.mark.parametrize(
    "system,code,parent",
    [
        ("EUNIS_M_2022", "MA1", "M"),
        ("EUNIS_M_2022", "MA121", "MA12"),
        ("EUNIS_2012", "A1.1", "A1"),
        ("EUNIS_2012", "A1.11", "A1.1"),
    ],
)
def test_parent_codes(habitats, system, code, parent):
    row = habitats[(habitats.system == system) & (habitats.code == code)]
    assert row["parent_code"].iloc[0] == parent


# Gaps in the upstream terrestrial hierarchy (parent at level - 1 not present in the source)
KNOWN_ORPHANS = {("EUNIS_T_2021", "S361"), ("EUNIS_T_2021", "T12142")}


def test_no_empty_codes(habitats):
    assert habitats["code"].notna().all()


def test_every_non_root_has_parent(habitats):
    orphans = habitats[(habitats.level > 1) & habitats.parent_code.isna()]
    found = set(zip(orphans.system, orphans.code))
    assert found <= KNOWN_ORPHANS, sorted(found - KNOWN_ORPHANS)
    assert not orphans.system.str.startswith("EUNIS_M").any()
