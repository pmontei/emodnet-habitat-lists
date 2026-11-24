"""GOOS Biology and Ecosystems Essential Ocean Variables (EOV) relevant to seabed habitats.

System produced
---------------
``GOOS_EOV``
    The four habitat EOVs of the GOOS specification sheets (version August 2026), level 1, with their
    definition; their sub-variables ("key measurements that are used to estimate the EOV") as level 2,
    with code ``<eov>/<sub-variable>``. Transcribed from the sheets (``EOVS``); every name is checked
    against the PDF text by the tests.

The coral EOV is now "Coral Cover and Composition" and covers shallow and deep-water corals
(hard corals, soft corals, black corals); it replaces "Hard coral cover and composition", the name
still used by the JNCC correlation tables ("Hard coral cover"), which are mapped to the new code.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import HABITATS_COLUMNS
from .msfd_bht import slug

FOLDER = "16.GOOS EOV"

EOVS = {
    "coral-cover-and-composition": {
        "name": "Coral Cover and Composition", "file": "01_2026_*Coral*.pdf", "doc": "GOOS Document No. 325",
        "definition": None,   # the sheet's DEFINITION field repeats the sub-variables
        "sub": ["Percent Living and/or Dead Coral Cover (on available substrate)",
                "Taxonomic or Morphotype Composition",
                "Coral Reef Benthic Area (the total spatial footprint",
                "Coral Condition and Health (e.g., bleaching, disease, mortality, other disturbances)"],
        "notes": "covers shallow and deep-water corals (Scleractinia, Stylasteridae, Milleporidae, Octocorallia, "
                 "Antipatharia); 'Coral Reef Benthic Area (the total spatial footprint' is truncated in the sheet",
    },
    "seagrass-cover-and-composition": {
        "name": "Seagrass Cover and Composition", "file": "02_2026_*Seagrass*.pdf", "doc": "GOOS Document No. 322",
        "definition": "This EOV characterises the areal extent, cover, and species composition of the submerged "
                      "plants that form the foundation of seagrass habitats and ecosystems.",
        "sub": ["Percent Cover", "Taxonomic Composition", "Areal Extent"], "notes": "",
    },
    "macroalgal-canopy-cover-and-composition": {
        "name": "Macroalgal Canopy Cover and Composition", "file": "03_2026_*Macroalgal*.pdf",
        "doc": "GOOS Document No. 329",
        "definition": "This EOV characterises the living cover and taxonomic and functional composition of "
                      "canopy-forming macroalgae across marine and coastal habitats, encompassing all macroalgal "
                      "species that form the structurally dominant upper layer regardless of taxonomy.",
        "sub": ["Canopy Percent Cover", "Canopy Taxonomic Composition", "Areal Extent", "Macroalgal stipe density"],
        "notes": "",
    },
    "mangrove-cover-and-composition": {
        "name": "Mangrove Cover and Composition", "file": "04_2026_*Mangrove*.pdf", "doc": "GOOS Document No. 323",
        "definition": "This EOV characterises the areal extent and tree species composition of mangrove communities "
                      "and their associated species across intertidal and shallow coastal habitats.",
        "sub": ["Areal extent", "Taxonomic Composition, including associated species (e.g. buttonwood, sea hibiscus, "
                "etc)", "Tree Height and Diameter at Breast Height"],
        "notes": "",
    },
}
SRC = "Global Ocean Observing System (2026). Essential Ocean Variable Specification Sheet: {name}. {doc}. Version August 2026"
# names used by other sources for these EOVs
ALIASES = {"hard coral cover": "coral-cover-and-composition", "hard coral cover and composition":
           "coral-cover-and-composition", "seagrass": "seagrass-cover-and-composition",
           "seagrass cover": "seagrass-cover-and-composition", "macroalgal canopy":
           "macroalgal-canopy-cover-and-composition", "macroalgal canopy cover":
           "macroalgal-canopy-cover-and-composition", "mangrove": "mangrove-cover-and-composition",
           "mangrove cover": "mangrove-cover-and-composition"}


def code_for(name: str) -> str | None:
    n = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    if slug(name) in EOVS:
        return slug(name)
    return ALIASES.get(n)


def pdf_text(sources: Path, code: str) -> str:
    files = sorted((sources / FOLDER).glob(EOVS[code]["file"]))
    if not files:
        raise FileNotFoundError(f"{sources / FOLDER}/{EOVS[code]['file']}")
    return "\n".join(pdftext.pdf_to_lines(files[0], layout=False))


def habitats() -> pd.DataFrame:
    rows = []
    for code, e in EOVS.items():
        src = SRC.format(name=e["name"], doc=e["doc"])
        rows.append({"system": "GOOS_EOV", "code": code, "name": e["name"], "level": 1, "parent_code": None,
                     "realm": "marine", "group": "EOV", "description": e["definition"], "source": src,
                     "notes": e["notes"]})
        for s in e["sub"]:
            short = re.sub(r"\s*\(.*$|,.*$", "", s)
            rows.append({"system": "GOOS_EOV", "code": f"{code}/{slug(short)}", "name": s, "level": 2,
                         "parent_code": code, "realm": "marine", "group": "EOV sub-variable", "description": None,
                         "source": src + ", section 1 (EOV sub-variables)", "notes": ""})
    df = pd.DataFrame(rows)
    df["level"] = df["level"].astype("Int64")
    return df[HABITATS_COLUMNS]
