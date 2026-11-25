from pathlib import Path

import pandas as pd
import pytest

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
pytestmark = pytest.mark.skipif(not (PROCESSED / "list_members.csv").is_file(), reason="run ehl-build first")


def _read(name):
    return pd.read_csv(PROCESSED / f"{name}.csv", dtype=str)


def test_lists_are_not_systems():
    systems, habitats, cw = _read("systems"), _read("habitats"), _read("crosswalks")
    lists = {"EMODNET_BIOGENIC_2021", "GOOS_EOV", "NRL_2024", "UK_PMF", "UK_MCZ_FOCI", "UK_HPI", "UK_MCZ_BSH",
             "BARCELONA_RL_2019", "EMODNET_OSPAR2025"}
    assert not set(systems.system) & lists and not set(habitats.system) & lists
    assert not (set(cw.from_system) | set(cw.to_system)) & lists
    assert set(_read("lists").list_id) >= {"EMODNET_BIOGENIC", "GOOS_EOV", "NRL_2024_MARINE", "CORALLIGENOUS", "EFH",
                                           "UK_PMF", "UK_MCZ_FOCI", "UK_HPI", "UK_MCZ_BSH", "BARCELONA_RL_2019",
                                           "EMODNET_OSPAR2025"}


def test_members_resolve():
    m, items = _read("list_members"), _read("list_items")
    assert set(zip(m.list_id, m["item"])) <= set(zip(items.list_id, items["item"]))
    assert set(m.link_type) <= {"member", "partial", "supports function", "excluded"}
    assert set(m.status) <= {"published", "proposed", "reviewed", "rejected"}
    # only the report's own corrections of EUNIS 2019 are unresolved codes
    bad = m[m.notes.fillna("").str.contains("not found in")]
    # the report's own corrections of EUNIS 2019, and the JNCC v22.04 code missing from the biotope list
    others = bad[bad.list_id != "EOV_SEAGRASS"]
    assert set(others.code) == {"MB2224", "MC223", "MC2237", "MC2238", "M.AtMB.Sa.InfPol"}
    # EOV_SEAGRASS: wrong codes of the D3.11 (2025) table, kept as rejected rows
    sg = bad[bad.list_id == "EOV_SEAGRASS"]
    assert set(sg.status) == {"rejected"} and set(sg.code) == {"III.5.2", "III.5.3", "III.5.4", "III.5.5", "III.5.6",
                                                               "MB2.55", "MB2.56"}


def test_nrl_marine():
    m = _read("list_members")
    nrl = m[m.list_id == "NRL_2024_MARINE"]
    assert len(nrl) == 231 and set(nrl.system) == {"EUNIS_M_2022"} and set(nrl.status) == {"published"}
    assert ("G1-MED", "MB252", "Mediterranean") in set(zip(nrl["item"], nrl.code, nrl.region))


def test_biogenic_eunis2022_proposal():
    m = _read("list_members")
    b = m[(m.list_id == "EMODNET_BIOGENIC") & (m.system == "EUNIS_M_2022")]
    assert set(b.status) == {"proposed"} and b.code.nunique() == 70
    assert {"MC223", "MC2235", "MC2236", "MB2223"} <= set(b.code)
    assert not {"MC2237", "MC2238", "MB2224"} & set(b.code)
    review = b[b.notes.str.contains("TO REVIEW", na=False)]
    assert set(review.code) == {"MB22", "MB222", "MB2223", "MC22", "MC221", "MC223"}
    assert "MC1281" in review[review.code == "MC221"].notes.iloc[0]
    # Annex I 1170 only for its biogenic subtype
    a = m[(m.list_id == "EMODNET_BIOGENIC") & (m.system == "ANNEX_I") & (m.code == "1170")]
    assert set(a.link_type) == {"partial"}


def test_former_systems_now_lists():
    m, items = _read("list_members"), _read("list_items")
    rl = m[m.list_id == "BARCELONA_RL_2019"]
    assert len(rl) == 267 and set(rl.system) == {"BARCELONA_2019"} and (rl["item"] == rl.code).all()
    pmf = items[items.list_id == "UK_PMF"]
    assert "blue-mussel-beds" in set(pmf["item"]) and "Blue mussel beds" in set(pmf.name)
    # list-to-list link: UK PMF item as member of a biogenic type
    assert ((m.list_id == "EMODNET_BIOGENIC") & (m.system == "UK_PMF") & (m.code == "blue-mussel-beds")).any()
    o = m[m.list_id == "EMODNET_OSPAR2025"]
    assert len(o) == 30 and set(o.system) == {"OSPAR_TD_2021"}


def test_list_roles():
    from emodnet_habitat_lists.lists import ROLES
    lists = _read("lists")
    assert set(lists.role) == ROLES
    obj = lists[lists.role == "objective"]
    assert (obj.deliverable.str.match(r"D3\.\d")).all()
    assert {"EMODNET_BIOGENIC", "EOV_SEAGRASS", "EOV_CORAL", "EOV_MACROALGAE", "VME", "EFH"} <= set(obj.list_id)
    assert not (lists[lists.role == "possible"].status == "planned").any()
