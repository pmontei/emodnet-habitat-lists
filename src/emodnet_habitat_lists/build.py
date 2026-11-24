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
from .schema import CROSSWALKS_COLUMNS, EXTRACTION_RULES_COLUMNS, HABITATS_COLUMNS, SYSTEMS_COLUMNS
from .sources import annex_i, barcelona, bern, biogenic, carib, ramsar, redlist, eunis_habitats, helcom_hub, ices_vme, jncc_mhc, msfd_bht, nrl, ospar

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
    ("OSPAR_TD_2021", "OSPAR List of Threatened and/or Declining Habitats (habitats and sub-types)", "2021",
     "OSPAR Commission", "North-East Atlantic", ospar.SRC_LIST + "; " + ospar.SRC_DESC),
    ("ICES_VME", "ICES VME habitat types and subtypes", "2023", "ICES", "North Atlantic, deep sea", ices_vme.SRC),
    ("HELCOM_HUB", "HELCOM Underwater Biotope and habitat classification (HUB)", "2013", "HELCOM", "Baltic Sea",
     helcom_hub.SRC_139 + "; " + helcom_hub.SRC_138 + "; HELCOM HUB fact sheets"),
    ("HELCOM_1998", "HELCOM Red List of marine and coastal biotopes and biotope complexes (classification of 1998)",
     "1998", "HELCOM", "Baltic Sea", "not loaded; codes appear in crosswalks only (from HUB fact sheets)"),
    ("UK_MHC_2204", "Marine Habitat Classification for Britain and Ireland", "22.04", "JNCC", "UK and Ireland",
     jncc_mhc.SRC_LIST),
    ("UK_MHC_1503", "Marine Habitat Classification for Britain and Ireland", "15.03", "JNCC", "UK and Ireland",
     "not loaded; codes appear in crosswalks only (" + jncc_mhc.SRC_CORR + ")"),
    ("UK_MNCR_0405", "Marine Habitat Classification for Britain and Ireland", "04.05", "JNCC", "UK and Ireland",
     "not loaded; codes appear in crosswalks only (OSPAR Agreement 2008-07; " + jncc_mhc.SRC_CORR + ")"),
    ("UK_MHC_9706", "Marine Habitat Classification for Britain and Ireland (MNCR BioMar)", "97.06", "JNCC",
     "UK and Ireland", "not loaded; codes appear in crosswalks only (" + jncc_mhc.SRC_CORR + ")"),
    ("UK_HPI", "Habitats of Principal Importance (UK)", "", "UK nature conservation bodies", "UK",
     "not loaded; names (slugs) appear in crosswalks only (" + jncc_mhc.SRC_CORR + ")"),
    ("UK_MCZ_FOCI", "Marine Conservation Zone habitat Features of Conservation Importance", "", "Defra / JNCC",
     "England, Wales, UK offshore", "not loaded; names (slugs) appear in crosswalks only (" + jncc_mhc.SRC_CORR + ")"),
    ("UK_PMF", "Priority Marine Features (Scotland)", "", "NatureScot / JNCC", "Scotland",
     "not loaded; names (slugs) appear in crosswalks only (" + jncc_mhc.SRC_CORR + ")"),
    ("UK_MCZ_BSH", "Marine Conservation Zone Broad-Scale Habitats", "", "Defra / JNCC", "England, Wales, UK offshore",
     "not loaded; names (slugs) appear in crosswalks only (" + jncc_mhc.SRC_CORR + ")"),
    ("RAMSAR", "Ramsar Classification System for Wetland Type", "Rev. COP14 (2022)", "Ramsar Convention",
     "global wetlands", ramsar.SRC),
    ("EU_REDLIST_2016", "European Red List of Habitats, marine habitats (EU28 / EU28+ assessments)", "2016",
     "European Commission", "EU28+ seas (Baltic, North-East Atlantic, Mediterranean, Black Sea)", redlist.SRC),
    ("EMERALD", "Bern Convention Resolution No. 4 (1996) habitats (Emerald Network), revised Annex I using EUNIS",
     "2019", "Council of Europe (Bern Convention)", "Bern Convention Contracting Parties", bern.SRC),
    ("GOOS_EOV", "GOOS biology and ecosystems Essential Ocean Variables", "", "GOOS", "global",
     "not loaded; names (slugs) appear in crosswalks only (" + jncc_mhc.SRC_CORR + ")"),
    ("IUCN_GET", "IUCN Global Ecosystem Typology", "2.x", "IUCN", "global",
     "not yet loaded; codes appear in crosswalks only"),
    ("EMODNET_BIOGENIC_2021", "EMODnet Seabed Habitats biogenic substrate types (composite data product D3.05/D3.06)",
     "2021", "EMODnet Seabed Habitats", "European seas", biogenic.SRC),
    ("CARIB_MARTINIQUE_2022", "Typologie des habitats benthiques de la Martinique (Andres et al.)", "2022",
     "PatriNat (OFB-CNRS-MNHN)", "Martinique (used by EUSeaMap for the Caribbean)", carib.SRC),
    ("FR_APHN_ANTILLES", "Habitats eligible for French prefectoral habitat protection orders (APHN), Antilles "
     "(typology of Hoff 1997)", "2019", "French Ministry of Ecology", "Guadeloupe, Martinique, Saint-Martin",
     "not loaded; codes appear in crosswalks only (" + carib.SRC_APHN + ")"),
    ("NRL_2024", "Nature Restoration Regulation (EU) 2024/1991, Annex II: groups of marine habitat types", "2024",
     "European Parliament and Council", "EU marine waters", nrl.SRC),
    ("EMODNET_OSPAR2025", "EMODnet Seabed Habitats OSPAR habitats dataset: habtype / habsubtype values", "2025",
     "EMODnet Seabed Habitats", "North-East Atlantic", ospar.SRC_EMODNET + "; codes appear in crosswalks only"),
    ("ANNEX_I", "Habitats Directive (92/43/EEC) Annex I natural habitat types", "2013 (EUR28)",
     "European Commission", "EU", annex_i.SRC_DIRECTIVE + "; " + annex_i.SRC_MANUAL),
    ("MSFD_BHT", "MSFD benthic broad habitat types", "2017", "European Commission", "EU marine waters, benthic",
     msfd_bht.SRC),
    ("PAL_CLASS", "Palaearctic habitat classification (Devillers & Devillers-Terschuren 1996)", "1996/1997",
     "Council of Europe", "Palaearctic", "not loaded; codes appear in crosswalks only (Interpretation Manual EUR28)"),
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
    rules: list[pd.DataFrame] = []
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

    if (sources / helcom_hub.FOLDER).is_dir() and pdftext.available():
        habitats.append(helcom_hub.habitats(sources))
        crosswalks.append(helcom_hub.crosswalk_fact_sheets(sources))
        eunis22 = sources / EUNIS_M_2022_XLSX
        if eunis22.is_file():
            crosswalks.append(helcom_hub.crosswalk_eunis2022_sources(eunis22))
        loaded.add("HELCOM_HUB")
    else:
        print(f"skipped HELCOM HUB: {sources / helcom_hub.FOLDER} not found or pdftotext not installed")
    if (sources / ospar.FOLDER).is_dir() and pdftext.available():
        habitats.append(ospar.habitats())
        crosswalks.append(ospar.crosswalks(sources))
        loaded.add("OSPAR_TD_2021")
    else:
        print(f"skipped OSPAR: {sources / ospar.FOLDER} not found or pdftotext not installed")
    if (sources / ices_vme.FOLDER / ices_vme.VOCAB_CSV).is_file():
        habitats.append(ices_vme.habitats(sources))
        loaded.add("ICES_VME")
    else:
        print(f"skipped ICES VME: {sources / ices_vme.FOLDER / ices_vme.VOCAB_CSV} not found")

    if (sources / annex_i.FOLDER).is_dir() and pdftext.available():
        habitats.append(annex_i.habitats(sources))
        crosswalks.append(annex_i.crosswalk_manual(sources))
        eunis22 = sources / EUNIS_M_2022_XLSX
        if eunis22.is_file():
            crosswalks.append(annex_i.crosswalk_eunis2022(eunis22))
        loaded.add("ANNEX_I")
    else:
        print(f"skipped Annex I: {sources / annex_i.FOLDER} not found or pdftotext not installed")
    if (sources / msfd_bht.FOLDER).is_dir() and pdftext.available():
        habitats.append(msfd_bht.habitats(sources))
        crosswalks.append(msfd_bht.crosswalk_eunis(sources))
        loaded.add("MSFD_BHT")
    else:
        print(f"skipped MSFD broad habitat types: {sources / msfd_bht.FOLDER} not found or pdftotext not installed")

    if (sources / biogenic.FOLDER).is_dir() and pdftext.available():
        habitats.append(biogenic.habitats(sources))
        crosswalks += [biogenic.crosswalk_appendix1(sources), biogenic.crosswalk_appendix2(sources),
                       biogenic.crosswalk_uk_lists()]
        rules.append(biogenic.extraction_rules())
        loaded.add("EMODNET_BIOGENIC_2021")
    else:
        print(f"skipped biogenic substrate: {sources / biogenic.FOLDER} not found or pdftotext not installed")
    if (sources / ramsar.FOLDER).is_dir() and list((sources / ramsar.FOLDER).glob(ramsar.CROSSWALK_GLOB)) \
            and pdftext.available():
        crosswalks.append(ramsar.crosswalk_get(sources))
        if list((sources / ramsar.FOLDER).glob(ramsar.FRAMEWORK_GLOB)):
            habitats.append(ramsar.habitats(sources))
            loaded.add("RAMSAR")
    if (sources / redlist.FOLDER).is_dir() and list((sources / redlist.FOLDER).glob(redlist.REPORT_GLOB)) \
            and pdftext.available():
        eunis22 = sources / EUNIS_M_2022_XLSX
        habitats.append(redlist.habitats(sources, eunis22))
        if eunis22.is_file():
            crosswalks.append(redlist.crosswalk_eunis2022(eunis22))
        loaded.add("EU_REDLIST_2016")
    else:
        print(f"skipped European Red List of Habitats: {sources / redlist.FOLDER} not found or pdftotext not installed")
    if (sources / bern.FOLDER).is_dir() and pdftext.available():
        habitats.append(bern.habitats(sources))
        annex_codes = set(annex_i.habitats(sources).code) if (sources / annex_i.FOLDER).is_dir() else None
        crosswalks += [bern.crosswalk_eunis(sources), bern.crosswalk_annex_i(sources, annex_codes)]
        loaded.add("EMERALD")
    else:
        print(f"skipped Bern Convention: {sources / bern.FOLDER} not found or pdftotext not installed")
    if (sources / carib.FOLDER).is_dir() and list((sources / carib.FOLDER).glob(carib.TYPOLOGY_GLOB)) \
            and pdftext.available():
        habitats.append(carib.habitats(sources))
        crosswalks.append(carib.crosswalk_aphn(sources))
        loaded.add("CARIB_MARTINIQUE_2022")
    else:
        print(f"skipped Caribbean (Martinique): {sources / carib.FOLDER} not found or pdftotext not installed")
    if (sources / nrl.FOLDER).is_dir() and pdftext.available():
        habitats.append(nrl.habitats(sources))
        crosswalks.append(nrl.crosswalks(sources))
        loaded.add("NRL_2024")
    else:
        print(f"skipped Nature Restoration Regulation: {sources / nrl.FOLDER} not found or pdftotext not installed")
    if (sources / jncc_mhc.FOLDER).is_dir():
        habitats.append(jncc_mhc.habitats(sources))
        so_far = pd.concat(habitats, ignore_index=True)
        crosswalks.append(jncc_mhc.crosswalks(sources, so_far[so_far.system == "OSPAR_TD_2021"],
                                              so_far[so_far.system == "ICES_VME"]))
        loaded.add("UK_MHC_2204")
    else:
        print(f"skipped JNCC Marine Habitat Classification: {sources / jncc_mhc.FOLDER} not found")

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
    rules_df = pd.concat(rules, ignore_index=True) if rules else pd.DataFrame(columns=EXTRACTION_RULES_COLUMNS)
    rules_df.to_csv(out / "extraction_rules.csv", index=False)
    return {"habitats": habitats_df, "crosswalks": crosswalks_df, "systems": systems, "extraction_rules": rules_df}


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
