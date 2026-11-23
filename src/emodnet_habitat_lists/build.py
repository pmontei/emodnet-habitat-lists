"""Build the reference tables into ``data/processed``.

Usage::

    ehl-build                                   # or: python -m emodnet_habitat_lists.build
    ehl-build --sources "path/to/classification systems" --out data/processed

``--sources`` is a folder with one sub-folder per classification system, laid out as described
in ``docs/sources.md``. Systems whose source files are missing are skipped with a message.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from . import pdftext
from .schema import CROSSWALKS_COLUMNS, HABITATS_COLUMNS, SYSTEMS_COLUMNS
from .sources import barcelona, eunis_habitats

EUNIS_M_2022_XLSX = (
    "1.EUNIS habitat classification/3_eea_t_eunis-hab-m_p_2004-2019_v01_r00/"
    "eea_t_eunis-hab-m_p_2004-2019_v01_r00/EUNIS marine habitat classification 2022 including crosswalks.xlsx"
)

SYSTEMS = [
    # system, name, version, authority, scope, source
    ("EUNIS_2012", "EUNIS habitat classification 2007, revised descriptions 2012 (amended 2019)", "2012", "EEA",
     "terrestrial + marine", eunis_habitats.SOURCE_LABEL),
    ("EUNIS_M_2019", "EUNIS marine habitat classification", "2019", "EEA", "marine", eunis_habitats.SOURCE_LABEL),
    ("EUNIS_M_2022", "EUNIS marine habitat classification", "2022", "EEA", "marine", eunis_habitats.SOURCE_LABEL),
    ("EUNIS_T_2021", "EUNIS terrestrial habitat classification", "2021", "EEA", "terrestrial",
     eunis_habitats.SOURCE_LABEL),
    ("BARCELONA_2019", "Updated Classification of Benthic Marine Habitat Types for the Mediterranean Region",
     "2019", "UNEP/MAP - SPA/RAC", "Mediterranean, benthic", barcelona.SRC_DECISION + ", Annex VI"),
    ("BARCELONA_RL_2019", "Updated Reference List of Marine Habitat Types for the Selection of Sites to be "
     "included in the National Inventories of Natural Sites of Conservation Interest in the Mediterranean",
     "2019", "UNEP/MAP - SPA/RAC", "Mediterranean, benthic", barcelona.SRC_DECISION + ", Annex VII"),
    ("BARCELONA_2006", "Classification of Benthic Marine Habitat Types for the Mediterranean Region (former)",
     "1998/2006", "UNEP/MAP - RAC/SPA", "Mediterranean, benthic", barcelona.SRC_2006),
    ("ANNEX_I", "Habitats Directive (92/43/EEC) Annex I habitat types", "", "European Commission", "EU",
     "not yet loaded; codes appear in crosswalks only"),
    ("CORINE", "CORINE biotopes", "1991", "European Commission", "Europe",
     "not yet loaded; codes appear in crosswalks only"),
]


def validate_crosswalks(cw: pd.DataFrame, habitats: pd.DataFrame) -> pd.DataFrame:
    """Flag crosswalk codes that do not exist in a loaded system."""
    known = {s: set(g["code"]) for s, g in habitats.groupby("system")}
    cw = cw.copy()
    for side in ("from", "to"):
        missing = [
            (s in known) and (c not in known[s])
            for s, c in zip(cw[f"{side}_system"], cw[f"{side}_code"])
        ]
        note = cw[f"{side}_system"].radd(f"{side}_code not found in ")
        cw.loc[missing, "notes"] = (cw.loc[missing, "notes"].fillna("") + "; " + note[missing]).str.lstrip("; ")
    return cw


def build(raw: Path, sources: Path, out: Path) -> dict[str, pd.DataFrame]:
    out.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    habitats = [eunis_habitats.load(eunis_habitats.fetch_rda(raw / "eunis_habitats.rda"))]
    crosswalks: list[pd.DataFrame] = []
    loaded = {"EUNIS_2012", "EUNIS_M_2019", "EUNIS_M_2022", "EUNIS_T_2021"}

    bc_dir = sources / barcelona.FOLDER
    if bc_dir.is_dir() and pdftext.available():
        habitats.append(barcelona.habitats(sources))
        manual = barcelona.crosswalk_manual(sources)
        crosswalks += [manual, barcelona.crosswalk_2006_2019_published()]
        loaded |= {"BARCELONA_2019", "BARCELONA_RL_2019", "BARCELONA_2006"}
        eunis22 = sources / EUNIS_M_2022_XLSX
        if eunis22.is_file():
            old_to_e22 = barcelona.crosswalk_eunis2022_sources(eunis22)
            all_hab = pd.concat(habitats, ignore_index=True)
            crosswalks += [old_to_e22, barcelona.crosswalk_2006_2019_candidates(old_to_e22, manual, all_hab)]
        else:
            print(f"skipped BARCELONA_2006 -> EUNIS_M_2022: {eunis22} not found")
    else:
        print(f"skipped Barcelona Convention: {bc_dir} not found or pdftotext not installed")

    habitats_df = pd.concat(habitats, ignore_index=True)[HABITATS_COLUMNS]
    crosswalks_df = (
        validate_crosswalks(pd.concat(crosswalks, ignore_index=True), habitats_df)[CROSSWALKS_COLUMNS]
        if crosswalks else pd.DataFrame(columns=CROSSWALKS_COLUMNS)
    )
    systems = pd.DataFrame(
        [
            {"system": s, "name": n, "version": v, "authority": a, "scope": sc, "source": src,
             "accessed": today if s in loaded else "", "notes": "" if s in loaded else "not loaded in this build"}
            for s, n, v, a, sc, src in SYSTEMS
        ],
        columns=SYSTEMS_COLUMNS,
    )

    habitats_df.to_csv(out / "habitats.csv", index=False)
    crosswalks_df.to_csv(out / "crosswalks.csv", index=False)
    systems.to_csv(out / "systems.csv", index=False)
    return {"habitats": habitats_df, "crosswalks": crosswalks_df, "systems": systems}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raw", type=Path, default=Path("data/raw"))
    p.add_argument("--sources", type=Path, default=Path("data/raw/sources"))
    p.add_argument("--out", type=Path, default=Path("data/processed"))
    a = p.parse_args(argv)
    tables = build(a.raw, a.sources, a.out)
    for name, df in tables.items():
        print(f"{name}: {len(df)} rows -> {a.out / (name + '.csv')}")
    print(tables["habitats"]["system"].value_counts().to_string())
    if len(tables["crosswalks"]):
        print(tables["crosswalks"].groupby(["from_system", "to_system", "relationship"]).size().to_string())


if __name__ == "__main__":
    main()
