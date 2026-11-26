import os
from pathlib import Path

import pandas as pd
import pytest

from emodnet_habitat_lists import eov_seagrass as sg
from emodnet_habitat_lists import pdftext

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
# folder with the EOV reports (WorkClaude/Reports/EOV); set EHL_REPORTS to run the PDF checks
REPORTS = Path(os.environ.get("EHL_REPORTS", ROOT / "data" / "raw" / "reports"))


def _read(name):
    return pd.read_csv(PROCESSED / name, dtype=str, keep_default_na=False)


@pytest.fixture(scope="module")
def tables():
    habitats, crosswalks, members = _read("habitats.csv"), _read("crosswalks.csv"), _read("list_members.csv")
    members = members[members.list_id != sg.LIST_ID]
    row, items, m = sg.build(habitats, crosswalks, members, "2026-11-25")
    return habitats, items, m, sg.filter_table(m, habitats)


def test_item_for():
    assert sg.item_for("Biocenosis of Posidonia oceanica") == "posidonia-beds"
    assert sg.item_for("Seagrass beds (other than Posidonia) on Mediterranean infralittoral sand") == "seagrass-beds"
    assert sg.item_for("Baltic photic sand dominated by common eelgrass (Zostera marina)") == "zostera-beds"
    assert sg.item_for("Herbiers à Halophila stipulacea sur sables", "CARIB_MARTINIQUE_2022") == "tropical-seagrass-beds"
    assert sg.item_for("Temperate [Halophila] and [Thalassia] beds") == "halophila-beds"
    assert sg.link_for_name("Sarmatic [Iris halophila] saline meadows")[0] == "excluded"
    assert sg.link_for_name("Dead matte of Posidonia oceanica")[0] == "member"
    assert sg.link_for_name("Association with [Caulerpa prolifera] on [Posidonia] beds")[0] == "member"
    assert sg.decision_for("Association with Caulerpa prolifera") is None   # no seagrass named
    assert sg.link_for_name("Association of Cymodocea nodosa or Caulerpa spp. with dead matte of Posidonia "
                            "oceanica")[0] == "member"


def test_published_codes_exist(tables):
    habitats, *_ = tables
    known = {s: set(g.code) for s, g in habitats.groupby("system")}
    assert set(sg.REPORT_2019_EUNIS) <= known["EUNIS_2012"]
    for spec in sg.REPORT_2025.values():
        for system, printed, _ in spec["codes"]:
            for code in sg._expand(printed, habitats, system):
                assert code in known[system] or (system, printed) in sg.REPORT_2025_ERRORS, (system, printed)


def test_report_errors_are_real(tables):
    habitats, *_ = tables
    names = dict(zip(zip(habitats.system, habitats.code), habitats.name))
    for system, code in sg.REPORT_2025_ERRORS:
        name = names.get((system, code), "")
        assert not sg.SEAGRASS_NAME.search(name), (system, code, name)


def test_filter(tables):
    _, items, members, f = tables
    use = dict(zip(zip(f.system, f.code), f.use))
    for key in [("EUNIS_M_2022", "MB252"), ("EUNIS_M_2022", "MB5223"), ("EUNIS_M_2022", "MA5221"),
                ("HELCOM_HUB", "AA.J1B7"), ("ANNEX_I", "1120"), ("BARCELONA_2019", "MB2.54"),
                ("BARCELONA_2019", "MB5.521"), ("OSPAR_TD_2021", "zostera-beds"),
                ("UK_MHC_2204", "SS.SMp.SSgr.Zmar"), ("CARIB_MARTINIQUE_2022", "C4-34.2")]:
        assert use.get(key) == "yes", key
    assert use[("ANNEX_I", "1110")] == "broader"
    for key in [("BARCELONA_2019", "MB2.53"), ("EUNIS_2012", "E6.2273")]:
        assert use[key] == "no", key
    for key in [("EUNIS_2012", "A5.5354"), ("EUNIS_M_2022", "MB2524"), ("BARCELONA_2006", "III.5.1.4")]:
        assert use[key] == "yes", key   # WP3 decision 26/11/2026: Caulerpa with seagrass is kept
    for key in [("BARCELONA_2019", "MB2.544"), ("EUNIS_M_2022", "MB2523"), ("EUNIS_M_2022", "MA2561"),
                ("EUNIS_2012", "A5.5353"), ("EUNIS_2012", "A2.131")]:   # WP3 decision: dead Posidonia included
        assert use[key] == "yes", key
    assert set(members["item"]) <= set(items["item"])
    assert f.set_index(["system", "code"]).index.is_unique
    # no proposed member without a reason to be there
    assert (members[members.status == "reviewed"].decided_by == sg.DECIDED_BY).all()
    prop = members[members.status == "proposed"]
    assert (prop.notes != "").all() and (prop.decided_by != "").all()


@pytest.mark.skipif(not REPORTS.is_dir() or not pdftext.available(), reason="EOV reports or pdftotext not available")
def test_codes_in_reports():
    t19 = sg.report_text(REPORTS, sg.REPORT_2019_GLOB)
    for code in sg.REPORT_2019_EUNIS:
        assert f" {code} " in t19, code
    for _, code, printed, _ in sg.REPORT_2019_OTHER:
        assert sg._norm(printed) in t19, printed
    # cells wrap inside codes, and the hyphen at a line break is dropped ("AA-" + "H1B7" -> "AAH1B7")
    squash = lambda x: "".join(sg._norm(x).split()).replace("-", "")
    t25 = squash(sg.report_text(REPORTS, sg.REPORT_2025_GLOB, layout=False))
    for spec in sg.REPORT_2025.values():
        for _, printed, _ in spec["codes"]:
            if printed in {"zostera-beds", "cymodocea-meadows"}:
                continue
            assert squash(printed) in t25, printed


@pytest.mark.skipif(not REPORTS.is_dir() or not pdftext.available(), reason="EOV reports or pdftotext not available")
def test_extraction_sources_in_report():
    squash = lambda x: "".join(sg._norm(x).split()).replace("-", "").lower()
    t25 = squash(sg.report_text(REPORTS, sg.REPORT_2025_GLOB, layout=False))
    for region, ds, scope, q, src, notes in sg.EXTRACTION_RULES:
        if src.endswith("Table 3"):
            assert squash(ds) in t25, ds


def test_extraction_rules_table():
    r = sg.extraction_rules()
    assert set(r.list_id) == {sg.LIST_ID} and set(r["item"]) == {"seagrass"} and len(r) == len(sg.EXTRACTION_RULES)
