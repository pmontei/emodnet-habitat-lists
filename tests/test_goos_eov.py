from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import goos_eov

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"


def test_habitats():
    h = goos_eov.habitats()
    assert h.code.is_unique and len(h[h.level == 1]) == 4 and len(h[h.level == 2]) == 14
    assert goos_eov.code_for("Hard coral cover") == "coral-cover-and-composition"


@pytest.mark.skipif(not (SOURCES / goos_eov.FOLDER).is_dir() or not pdftext.available(),
                    reason="GOOS EOV sheets or pdftotext not available")
def test_names_in_sheets():
    norm = lambda s: " ".join(s.split())
    for code, e in goos_eov.EOVS.items():
        text = norm(goos_eov.pdf_text(SOURCES, code))
        for s in [e["name"], *e["sub"]] + ([e["definition"]] if e["definition"] else []):
            assert norm(s) in text, (code, s)
