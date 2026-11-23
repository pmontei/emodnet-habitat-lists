from pathlib import Path

import pandas as pd
import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import ices_vme, jncc_mhc, nrl, ospar

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"


@pytest.mark.skipif(not (SOURCES / nrl.FOLDER).is_dir() or not pdftext.available(),
                    reason="Nature Restoration Regulation or pdftotext not available")
def test_nrl_annex_ii():
    h = nrl.habitats(SOURCES)
    assert set(h[h.level == 1].code) == {f"G{i}" for i in range(1, 8)}
    cw = nrl.crosswalks(SOURCES)
    groups = cw[cw.from_system == "NRL_2024"]
    assert len(groups) == 231
    assert not groups.notes.str.contains("ELI:|OJ L").any()          # page footers not in names
    assert set(groups[groups.from_code == "G1-MED"].to_code) >= {"MB252", "MB2521", "MB5545"}
    assert set(groups[groups.from_code == "G6-ATL"].to_code)          # vents and seeps: Atlantic only
    annex = cw[(cw.from_system == "EUNIS_M_2022") & (cw.from_code == "MA332")]
    assert set(annex.to_code) == {"1130", "1160", "1610", "1620"}     # wrapped name, codes on first line


@pytest.mark.skipif(not (SOURCES / jncc_mhc.FOLDER).is_dir(), reason="JNCC sources not available")
def test_jncc_mhc():
    h = jncc_mhc.habitats(SOURCES)
    assert len(h) == 694 and h.code.is_unique
    assert set(h[h.parent_code.isna()].level) == {2}
    o = ospar.habitats()
    v = ices_vme.habitats(SOURCES) if (SOURCES / ices_vme.FOLDER).is_dir() else pd.DataFrame(columns=["code", "name"])
    cw = jncc_mhc.crosswalks(SOURCES, o, v)
    assert set(cw.relationship) <= {"=", "<", ">", "#", "unspecified"}
    assert not cw.notes.str.contains("not matched").any()
    assert set(cw[cw.to_system == "OSPAR_TD_2021"].to_code) <= set(o.code)
    assert set(cw[cw.to_system == "GOOS_EOV"].to_code) == {"seagrass", "macroalgal-canopy", "hard-coral-cover"}
    assert set(cw[(cw.from_code == "LR") & (cw.to_system == "EUNIS_M_2022")].to_code) == {"MA1", "MA12"}
