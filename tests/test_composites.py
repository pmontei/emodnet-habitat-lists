from pathlib import Path

import pandas as pd
import pytest

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
COMP = PROCESSED / "composites.csv"


@pytest.mark.skipif(not COMP.is_file(), reason="run ehl-build first")
def test_biogenic_eunis2022():
    c = pd.read_csv(COMP, dtype=str)
    b = c[c.composite == "BIOGENIC_SUBSTRATE"]
    assert set(b.system) == {"EUNIS_M_2022"} and b.code.is_unique and len(b) == 70
    h = pd.read_csv(PROCESSED / "habitats.csv", dtype=str)
    assert set(b.code) <= set(h[h.system == "EUNIS_M_2022"].code)
    inc = dict(zip(b.code, b.include))
    # report corrections resolved in EUNIS 2022
    assert inc["MC223"] == "review" and inc["MC2235"] == "yes" and inc["MC2236"] == "yes"
    assert inc["MB2223"] == "review" and "MC2237" not in inc and "MB2224" not in inc
    # Sabellaria spinulosa encrusted rock left the biogenic worm reefs in 2022
    assert "MC1281" in b.set_index("code").rationale["MC221"]
    assert inc["MB252"] == "yes" and inc["MC251"] == "yes"
