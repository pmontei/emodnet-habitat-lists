"""Classes of global Earth-observation habitat maps used for the EOV products.

Systems produced
----------------
``ALLEN_CORAL_ATLAS_BENTHIC``
    The six benthic habitat map classes of the Allen Coral Atlas (v3 class descriptions, after
    Roelfsema et al. 2013) plus "Unknown". ``description`` is the one-line definition of each class;
    the "also goes by" names are kept in ``notes``.
``GMW_V3``
    Global Mangrove Watch v3.0 (Bunting et al. 2022): the two extent classes (mangrove,
    non-mangrove) and the two change classes (gain, loss).

Crosswalks produced (``candidate``: proposed by this repository, to be reviewed)
-------------------------------------------------------------------------------
Allen Coral Atlas and GMW classes -> ``GOOS_EOV``, ``IUCN_GET`` and ``RAMSAR``, for the EOV products.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS

ACA_FOLDER = "18.Allen Coral Atlas"
ACA_GLOB = "01_2020_*benthic-maps*.pdf"
GMW_FOLDER = "19.Global Mangrove Watch"
GMW_GLOB = "01_2022_*Global-Mangrove-Watch*.pdf"
SRC_ACA = ("Allen Coral Atlas. Benthic map classes: description of the shallow coral reef benthic mapping categories "
           "for Allen Coral Atlas global benthic habitat maps (v3), after Roelfsema et al. (2013)")
SRC_GMW = ("Bunting, P. et al., 2022. Global Mangrove Extent Change 1996-2020: Global Mangrove Watch Version 3.0. "
           "Remote Sensing 14(15): 3657, doi:10.3390/rs14153657")
SRC_CANDIDATE = "this repository (proposal for the WP3 EOV products, to be reviewed)"

# (code, name, definition, also goes by)
ACA = [
    ("coral-algae", "Coral Habitat (Coral/Algae)", "Coral Habitat is any hardbottom area supporting living coral and/or algae.",
     "Coral / Algae; Coral dominated; Coral framework; Hardbottom; Hard Coral; Stony Coral; Live Coral; Coral Reef; "
     "Mixed coral; Coral; Coral field; Carbonate framework"),
    ("sand", "Sand", "Sand includes any soft-bottom area dominated by fine unconsolidated sediments.",
     "Sand dominated; Bioclastic Sand; Sand and sparse algae; Coral Sand; Fine Sediment; Detrital Sand; Sand with "
     "Scattered Coral and Rock; Biogenic sand"),
    ("rubble", "Rubble", "Rubble is any habitat featuring loose, rough fragments of broken reef material.",
     "Rubble-Dominated; Skeletal Rubble; Coral Gravel; Coral Rudstone; Reef Rubble; Rhodoliths; Unconsolidated substrate"),
    ("rock", "Rock", "Rock is any exposed hardbottom area with uncommon to scarce corals and fleshy macroalgae.",
     "Rock dominated; Bedrock; Pavement; Rock Outcrop; Boulder; Beach Rock; Uncolonised hardbottom"),
    ("seagrass", "Seagrass", "Seagrass is any habitat where seagrass is the dominant biota.",
     "Seagrass Meadow; Seagrass Bed; Seagrass Dominated; Phanerogam Beds"),
    ("microalgal-mat", "Microalgal Mat",
     "Microalgal Mats are visible accumulations of microscopic algae in sandy sediments.",
     "Benthic Microalgae; BMA; Cyanobacterial Mats; Filamentous Algal Mat"),
    ("unknown", "Unknown", "Unknown may be assigned to an area on the map if a data constraint means it is not "
     "allocated a Global Benthic Class.", ""),
]
GMW = [("mangrove", "Mangrove", "extent"), ("non-mangrove", "Non-mangrove", "extent"),
       ("gain", "Mangrove gain", "change"), ("loss", "Mangrove loss", "change")]

CANDIDATES = [
    ("ALLEN_CORAL_ATLAS_BENTHIC", "coral-algae", "GOOS_EOV", "coral-cover-and-composition", "#",
     "class includes algae-dominated hard bottom; shallow reefs only (<~10-15 m)"),
    ("ALLEN_CORAL_ATLAS_BENTHIC", "seagrass", "GOOS_EOV", "seagrass-cover-and-composition", "<", ""),
    ("ALLEN_CORAL_ATLAS_BENTHIC", "coral-algae", "IUCN_GET", "M1.3", "#", "Photic coral reefs"),
    ("ALLEN_CORAL_ATLAS_BENTHIC", "seagrass", "IUCN_GET", "M1.1", "<", "Seagrass meadows"),
    ("ALLEN_CORAL_ATLAS_BENTHIC", "coral-algae", "RAMSAR", "C", "#", "Coral reefs"),
    ("ALLEN_CORAL_ATLAS_BENTHIC", "seagrass", "RAMSAR", "B", "<", "Marine subtidal aquatic beds"),
    ("GMW_V3", "mangrove", "GOOS_EOV", "mangrove-cover-and-composition", "<", "GMW gives extent only"),
    ("GMW_V3", "mangrove", "IUCN_GET", "MFT1.2", "=", "Intertidal forests and shrublands"),
    ("GMW_V3", "mangrove", "RAMSAR", "I", "<", "Intertidal forested wetlands (also nipah and tidal freshwater swamps)"),
]


def habitats(sources: Path) -> pd.DataFrame:
    rows = []
    if (sources / ACA_FOLDER).is_dir():
        for code, name, definition, aka in ACA:
            rows.append({"system": "ALLEN_CORAL_ATLAS_BENTHIC", "code": code, "name": name, "level": 1,
                         "parent_code": None, "realm": "marine", "group": "benthic", "description": definition,
                         "source": SRC_ACA, "notes": f"also goes by: {aka}" if aka else ""})
    if (sources / GMW_FOLDER).is_dir():
        for code, name, group in GMW:
            rows.append({"system": "GMW_V3", "code": code, "name": name, "level": 1, "parent_code": None,
                         "realm": "marine", "group": group, "description": None, "source": SRC_GMW, "notes": ""})
    df = pd.DataFrame(rows, columns=HABITATS_COLUMNS)
    df["level"] = df["level"].astype("Int64")
    return df


def crosswalks(sources: Path) -> pd.DataFrame:
    present = {s for s, f in (("ALLEN_CORAL_ATLAS_BENTHIC", ACA_FOLDER), ("GMW_V3", GMW_FOLDER))
               if (sources / f).is_dir()}
    rows = [{"from_system": a, "from_code": b, "to_system": c, "to_code": d, "relationship": "candidate",
             "source": SRC_CANDIDATE, "notes": f"proposed relationship '{rel}'" + (f"; {n}" if n else "")}
            for a, b, c, d, rel, n in CANDIDATES if a in present]
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


def aca_text(sources: Path) -> str:
    return "\n".join(pdftext.pdf_to_lines(sorted((sources / ACA_FOLDER).glob(ACA_GLOB))[0], layout=False))
