import re
from pathlib import Path

import pandas as pd
import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import helcom1998, jncc_mhc

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"
PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
PDF = helcom1998.find_pdf(SOURCES) if (SOURCES / helcom1998.FOLDER).is_dir() else None


@pytest.mark.skipif(PDF is None or not pdftext.available(), reason="HELCOM BSEP 75 PDF not available")
def test_helcom_1998():
    h = helcom1998.habitats(SOURCES)
    assert h.code.is_unique and len(h) == 202
    assert set(h.parent_code.dropna()) <= set(h.code)
    assert (h.realm == "marine").sum() == 101
    n = dict(zip(h.code, h.name))
    assert n["2.8.1"] == "Mixed sediments of the aphotic zone"
    assert n["2.10.2.1"] == "Sublittoral bubbling reefs with little or no macrophyte vegetation of the photic zone"
    assert not h.name.str.contains(r"\b(?:X|CP|CW|RUPE)\b").any()
    # names of the missing page are printed elsewhere in the same report
    text = re.sub(r"\s+", " ", " ".join(pdftext.pdf_to_lines(PDF, layout=False))).replace("ma- crophyte", "macrophyte")
    for code, (name, _) in {**helcom1998.MISSING_PAGE}.items():
        assert name in text, code
    for code, name in helcom1998.NAME_FIXES.items():
        assert name in text.replace("including", "incl."), code


@pytest.mark.skipif(not (SOURCES / jncc_mhc.FOLDER).is_dir(), reason="JNCC sources not available")
def test_jncc_former_versions():
    h = jncc_mhc.old_versions_habitats(SOURCES)
    n = h.system.value_counts()
    assert n["UK_MNCR_0405"] == 474          # 5 + 24 + 75 + 370 (v04.05 introduction)
    assert n["UK_MHC_9706"] == 322           # of 364 types (Report 229, Table 2.4)
    assert n["UK_MHC_1503"] in (688, 690)    # + M and M.AtMB.Bi from Report 530 Appendix 2
    v0405 = h[h.system == "UK_MNCR_0405"]
    assert v0405.level.value_counts().to_dict() == {5: 262, 6: 108, 4: 75, 3: 24, 2: 5}


@pytest.mark.skipif(not (PROCESSED / "crosswalks.csv").is_file(), reason="run ehl-build first")
def test_former_version_codes_resolve():
    c = pd.read_csv(PROCESSED / "crosswalks.csv", dtype=str)
    bad = c[c.notes.fillna("").str.contains(r"to_code not found in (?:UK_MNCR_0405|UK_MHC_9706|HELCOM_1998)")]
    assert bad.empty, bad[["from_code", "to_system", "to_code"]].to_string()
