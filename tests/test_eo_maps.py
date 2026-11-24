from pathlib import Path

import pytest

from emodnet_habitat_lists import pdftext
from emodnet_habitat_lists.sources import eo_maps

SOURCES = Path(__file__).resolve().parents[1] / "data" / "raw" / "sources"


@pytest.mark.skipif(not (SOURCES / eo_maps.ACA_FOLDER).is_dir() or not pdftext.available(),
                    reason="Allen Coral Atlas class descriptions not available")
def test_aca_definitions_in_pdf():
    norm = lambda s: " ".join(s.replace("-\n", "").split())
    text = norm(eo_maps.aca_text(SOURCES))
    for _, name, definition, _ in eo_maps.ACA:
        assert norm(definition) in text, name


def test_candidates_point_to_known_codes():
    from emodnet_habitat_lists.sources import goos_eov
    eov = {c for c in goos_eov.EOVS}
    for a, b, c, d, rel, n in eo_maps.CANDIDATES:
        if c == "GOOS_EOV":
            assert d in eov
