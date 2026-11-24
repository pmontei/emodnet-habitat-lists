"""EMODnet Seabed Habitats biogenic substrate typology (D3.06, 2021).

System produced
---------------
``EMODNET_BIOGENIC_2021``
    The four-level hierarchy of biogenic substrate types of Table 5 of the report (level 1
    "biogenic substrate"; level 2 e.g. "bivalve reefs"; level 3 e.g. "mussel beds"; level 4 e.g.
    "Modiolus modiolus beds"), with the regions where each type is thought to be present
    (Atlantic/Arctic, Baltic Sea, Black Sea, Mediterranean) in ``notes``. The report gives no
    codes: ``code`` is a slug of the name. The typology is transcribed (``TYPOLOGY``) and every
    name is checked against the PDF text by the tests.

Crosswalks produced
-------------------
* Appendix 1 (Tables 10-16): ``EUNIS_2012`` (EUNIS 2007-11), ``ANNEX_I``, ``HELCOM_HUB`` and
  ``OSPAR_TD_2021`` habitats ``-> EMODNET_BIOGENIC_2021``, relationship ``maps to`` (the
  habitat can be translated to that "most detailed biogenic substrate type"), region in ``notes``.
* Appendix 2 (Tables 17-21): ``EMODNET_BIOGENIC_2021 -> EUNIS_M_2019``, relationship
  ``maps to (with biological zone)``: the EUNIS 2019 habitat obtained from a biogenic substrate
  type in a given biological zone and region (zone, region, EUNIS 2007-11 code and the report's
  "unofficial corrections" of EUNIS 2019 in ``notes``).

Definition (report, section 1.1): biogenic substrate refers to beds or reefs of a species that,
like Mediterranean Posidonia oceanica meadows, cover and replace the underlying substrate, can
occur on different substrate types and are detectable with acoustic survey techniques.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import pdftext
from ..schema import CROSSWALKS_COLUMNS, EXTRACTION_RULES_COLUMNS, HABITATS_COLUMNS
from .msfd_bht import slug

FOLDER = "11.Biogenic substrate"
REPORT_GLOB = "01_2021_*Biogenic-substrate*.pdf"
SRC = ("Lillis, H., Allen, H., Agnesi, S., Annunziatellis, A. & Vasquez, M., 2021. A combined, harmonized data "
       "product showing the best evidence for the extent of biogenic substrate in Europe. EMODnet Seabed Habitats "
       "D3.05/D3.06")
DEFINITION = ("Beds or reefs of a species that, like Mediterranean Posidonia oceanica meadows, cover and replace the "
              "underlying substrate as a structuring factor, can occur on different substrate types, and are "
              "detectable using acoustic survey techniques (report, section 1.1).")

ATL, BAL, BLS, MED = "Atlantic/Arctic", "Baltic Sea", "Black Sea", "Mediterranean"
# (name, parent name, level, regions) - Table 5; '*' (observed but not forming reefs) in the note
TYPOLOGY = [
    ("biogenic substrate", None, 1, [ATL, BAL, BLS, MED]),
    ("bivalve reefs", "biogenic substrate", 2, [ATL, BAL, BLS, MED]),
    ("mussel beds", "bivalve reefs", 3, [ATL, BAL]),
    ("Modiolus modiolus beds", "mussel beds", 4, [ATL, BAL]),
    ("Mytilus edulis beds", "mussel beds", 4, [ATL, BAL]),
    ("dominated by zebra mussel", "mussel beds", 4, [BAL]),
    ("dominated by valve snails", "bivalve reefs", 3, [BAL]),
    ("Ostrea edulis beds", "bivalve reefs", 3, [ATL, BLS, MED]),
    ("Hiatella arctica beds", "bivalve reefs", 3, [ATL]),
    ("Limaria hians beds", "bivalve reefs", 3, [ATL, MED]),
    ("shell gravel", "biogenic substrate", 2, [ATL, BAL]),
    ("worm reefs", "biogenic substrate", 2, [ATL, MED]),
    ("Sabellaria alveolata reefs", "worm reefs", 3, [ATL, MED]),
    ("Sabellaria spinulosa reefs", "worm reefs", 3, [ATL, MED]),
    ("Serpula vermicularis reefs", "worm reefs", 3, [ATL]),
    ("peat bottoms", "biogenic substrate", 2, [BAL]),
    ("seagrass beds", "biogenic substrate", 2, [MED]),
    ("Posidonia oceanica meadows", "seagrass beds", 3, [MED]),
    ("live Posidonia oceanica meadows", "Posidonia oceanica meadows", 4, [MED]),
    ("dead mattes of Posidonia oceanica", "Posidonia oceanica meadows", 4, [MED]),
    ('Posidonia oceanica "Barrier-reef"', "Posidonia oceanica meadows", 4, [MED]),
    ("coralligenous platforms", "biogenic substrate", 2, [MED]),
    ("Facies with Vermetus of the infralittoral algae biocenosis", "biogenic substrate", 2, [MED]),
    ("Facies with Ficopomatus enigmaticus of the euryhaline and/or eurythermal lagoon biocenosis",
     "biogenic substrate", 2, [MED]),
    ("cold water coral reefs", "biogenic substrate", 2, [ATL, MED]),
    ("Desmophyllum pertusum (Lophelia pertusa) reefs", "cold water coral reefs", 3, [ATL, MED]),
    ("Solenosmilia variabilis reefs", "cold water coral reefs", 3, [ATL]),
    ("Madrepora oculata reefs", "cold water coral reefs", 3, [ATL, MED]),
    ("biogenic detritic bottoms", "biogenic substrate", 2, [BLS]),
]
TYPE_NOTES = {"Serpula vermicularis reefs": "Mediterranean: species observed but it does not form reefs (Table 5 '*')"}
# names used in the appendix tables that differ from Table 5
ALIASES = {
    "sabellaria spinulosa beds": "Sabellaria spinulosa reefs",    # Table 16 (OSPAR)
    "bivalve reefs unspecific": "bivalve reefs",                   # Table 15 footnote
    "mussel beds unspecific": "mussel beds",
}

_REGION_OF_TABLE = {"10": ATL, "11": BAL, "12": BLS, "13": MED, "14": "all regions", "15": BAL, "16": ATL,
                    "17": "Arctic", "18": "Atlantic", "19": BAL, "20": BLS, "21": MED}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


_BY_NORM = {_norm(n): n for n, *_ in TYPOLOGY} | {_norm(k): v for k, v in ALIASES.items()}


def type_code(name: str) -> str | None:
    n = _BY_NORM.get(_norm(name))
    return slug(n) if n else None


def _text(sources: Path) -> str:
    pdf = sorted((sources / FOLDER).glob(REPORT_GLOB))
    if not pdf:
        raise FileNotFoundError(f"{sources / FOLDER}/{REPORT_GLOB}")
    return "\n".join(pdftext.pdf_to_lines(pdf[0])).replace("\f", "\n")


def habitats(sources: Path | None = None) -> pd.DataFrame:
    rows = []
    for name, parent, level, regions in TYPOLOGY:
        notes = ["code is a slug of the name (no codes in the report)", "regions: " + ", ".join(regions)]
        if name in TYPE_NOTES:
            notes.append(TYPE_NOTES[name])
        rows.append({"system": "EMODNET_BIOGENIC_2021", "code": slug(name), "name": name, "level": level,
                     "parent_code": slug(parent) if parent else None, "realm": "marine", "group": "benthic",
                     "description": DEFINITION if level == 1 else None, "source": SRC + ", Table 5",
                     "notes": "; ".join(notes)})
    df = pd.DataFrame(rows)
    df["level"] = df["level"].astype("Int64")
    return df[HABITATS_COLUMNS]


def _tables(text: str) -> dict[str, list[str]]:
    """Lines of each appendix table, keyed by table number (page headers/footers removed)."""
    a = text.index("7 Appendix 1: Biogenic substrate crosswalks\n")
    noise = re.compile(r"EASME/EMFF/2018|A combined, harmonized data product|for the extent of biogenic substrate|"
                       r"^\s*\d{1,2}\s*$|European Marine Observation and Data Network|Regulation \(EU\) No 508/2014|"
                       r"European Maritime and Fisheries Fund")
    out: dict[str, list[str]] = {}
    cur = None
    for line in text[a:].split("\n"):
        if m := re.match(r"^Table (1[0-9]|2[01])\b", line):
            cur = m.group(1)
            out[cur] = []
            continue
        if re.match(r"^\d\.\d\s+[A-Z]", line):         # next appendix section: end of table
            cur = None
            continue
        if cur and not noise.search(line):
            out[cur].append(line)
    return out


_A1_ROW = re.compile(r"^((?:A\d[0-9A-Z.]*)|(?:A[AB]\.[A-Z][0-9A-Z]*\*?))\s+(\d)\s+(\S.*)$")


def crosswalk_appendix1(sources: Path) -> pd.DataFrame:
    tables = _tables(_text(sources))
    rows = []
    targets = {"10": "EUNIS_2012", "11": "EUNIS_2012", "12": "EUNIS_2012", "13": "EUNIS_2012", "15": "HELCOM_HUB"}
    for tab, system in targets.items():
        recs: list[list[str]] = []
        col = None          # start of the type column, taken from the last record line (varies by page)
        for line in tables[tab]:
            if not line.strip() or "Most detailed" in line or line.strip().startswith(("Code ", "7.")):
                continue
            fields = [(m.start(), m.group()) for m in re.finditer(r"\S+(?: \S+)*", line)]
            if _A1_ROW.match(line.strip()) and len(fields) >= 3:
                col = fields[-1][0]
                recs.append([fields[0][1].split()[0], fields[-1][1]])
            elif recs and col is not None:
                typ = " ".join(f for pos, f in fields if pos >= col - 3)
                if typ:
                    recs[-1][1] += " " + typ
        # Table 12 prints one name above its code ('Pontic Ostrea edulis biogenic reefs on mobile')
        for code, txt in recs:
            target = type_code(re.sub(r"\s+", " ", txt).strip())
            if target is None:
                raise ValueError(f"Table {tab}: unknown biogenic type for {code}: '{txt}'")
            notes = [f"region: {_REGION_OF_TABLE[tab]}"]
            star = code.endswith("*")
            code = code.rstrip("*")
            if star:
                notes.append("includes all child habitats except AA.E1E/AB.E1E (bivalve reefs) and AA.E1E1/AB.E1E1 "
                             "(mussel beds) (Table 15 footnote)")
            rows.append({"from_system": system, "from_code": code, "to_system": "EMODNET_BIOGENIC_2021",
                         "to_code": target, "relationship": "maps to",
                         "source": SRC + f", Appendix 1, Table {tab}", "notes": "; ".join(notes)})
    # Table 14: Habitats Directive Annex I
    rows.append({"from_system": "ANNEX_I", "from_code": "1120", "to_system": "EMODNET_BIOGENIC_2021",
                 "to_code": slug("Posidonia oceanica meadows"), "relationship": "maps to",
                 "source": SRC + ", Appendix 1, Table 14", "notes": "region: Mediterranean"})
    rows.append({"from_system": "ANNEX_I", "from_code": "1170", "to_system": "EMODNET_BIOGENIC_2021",
                 "to_code": slug("biogenic substrate"), "relationship": "maps to",
                 "source": SRC + ", Appendix 1, Table 14",
                 "notes": "region: all; Reefs - biogenic subtype only (not always explicit in Annex I habitat maps)"})
    # Table 16: OSPAR (names)
    ospar = {"Ostrea edulis beds": "ostrea-edulis-beds", "Modiolus modiolus Horse mussel beds": "modiolus-modiolus-beds",
             "Sabellaria spinulosa beds": "sabellaria-spinulosa-reefs", "Lophelia pertusa reefs": "lophelia-pertusa-reefs"}
    t16 = " ".join(tables["16"])
    for name, code in ospar.items():
        if name not in t16:
            raise ValueError(f"Table 16: '{name}' not found")
        target = {"Modiolus modiolus Horse mussel beds": "Modiolus modiolus beds",
                  "Lophelia pertusa reefs": "Desmophyllum pertusum (Lophelia pertusa) reefs"}.get(name, name)
        rows.append({"from_system": "OSPAR_TD_2021", "from_code": code, "to_system": "EMODNET_BIOGENIC_2021",
                     "to_code": type_code(target), "relationship": "maps to",
                     "source": SRC + ", Appendix 1, Table 16", "notes": f"region: {ATL}; OSPAR name in report: {name}"})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


_A2_ROW = re.compile(r"(\d)\s+(M[A-H][0-9A-Z]+)\s{2,}.*?\s(\d)\s+(A\d[0-9A-Z.]*)\s")
_FIELD = re.compile(r"\S+(?: \S+)*")


def _columns(header1: str, header2: str) -> list[tuple[int, str]]:
    """Column starts from the two header lines of an Appendix 2 table page."""
    cols = [(0, "zone"), (header1.index("Most detailed"), "type")]
    names = [m for m in re.finditer(r"Leve(?:l)?|Code|Habitat name|Description of", header2)]
    order = ["level1", "code1", "name1", "corr", "level2", "code2", "name2"]
    seq = [m.group() for m in names]
    if "Description of" not in seq:
        order.remove("corr")
    for m, key in zip(names, order):
        cols.append((m.start(), key))
    return sorted(cols)


def crosswalk_appendix2(sources: Path) -> pd.DataFrame:
    tables = _tables(_text(sources))
    rows = []
    for tab in ("17", "18", "19", "20", "21"):
        recs: list[dict] = []
        h1 = cols = None
        for line in tables[tab]:
            if "Most detailed" in line:
                h1 = line
                continue
            if "Habitat name" in line and h1 is not None:
                cols = _columns(h1, line)
                continue
            if cols is None or not line.strip() or re.match(r"^\s*(zone\b|substrate type|l\s*$|corrections)", line):
                continue
            fields = {}
            for f in _FIELD.finditer(line):
                if any(k == "corr" for _, k in cols):     # table with a corrections column: nearest header
                    key = min(cols, key=lambda c: abs(c[0] - f.start()))[1]
                else:                                      # names start well left of their header
                    start, key = max((c for c in cols if c[0] <= f.start() + 3), default=cols[0])
                    if key == "code1" and f.start() > start + 6:
                        key = "name1"
                fields[key] = (fields.get(key, "") + " " + f.group()).strip()
            m = _A2_ROW.search(line + " ")
            if m:
                recs.append({"level": m.group(1), "code": m.group(2), "e2007": m.group(4), **{
                    k: fields.get(k, "") for k in ("zone", "type", "name1", "corr")}})
            elif recs:
                for k in ("zone", "type", "name1", "corr"):
                    if fields.get(k):
                        recs[-1][k] = (recs[-1][k] + " " + fields[k]).strip()
        for r in recs:
            tname = re.sub(r"\s+", " ", r["type"]).strip()
            code = type_code(tname)
            if code is None:
                raise ValueError(f"Table {tab}: unknown biogenic type '{tname}' ({r['code']})")
            notes = [f"region: {_REGION_OF_TABLE[tab]}", "biological zone: " + re.sub(r"\s+", " ", r["zone"]).strip(),
                     f"EUNIS 2007-11: {r['e2007']}",
                     "EUNIS 2019 name in report: " + re.sub(r"\s+", " ", r["name1"]).strip()]
            corr = re.sub(r"\s+", " ", r["corr"]).strip()
            if corr:
                notes.append("report correction: " + corr)
            rows.append({"from_system": "EMODNET_BIOGENIC_2021", "from_code": code, "to_system": "EUNIS_M_2019",
                         "to_code": r["code"], "relationship": "maps to (with biological zone)",
                         "source": SRC + f", Appendix 2, Table {tab}", "notes": "; ".join(notes)})
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS)


# ---------------------------------------------------------------------------------------------
# Tables 6-9: most detailed biogenic substrate type, data source and query used to extract polygons
# ---------------------------------------------------------------------------------------------
EUNIS07 = "Individual habitat maps from surveys - EUNIS classification system (version 2007-11)"
ANNEX = "Individual habitat maps from surveys - Habitats Directive Annex I"
HUB = "Individual habitat maps from surveys - Other classification systems (i.e. HELCOM HUB)"
OSPAR20 = "OSPAR habitats - official 2020 public reference dataset"
GEMS = "Geodatabase of Marine features adjacent to Scotland (GeMS) V9 (i25) - Scottish Priority Marine Features (PMFs)"
NE_FOCI = "Natural England Marine Evidence Base - MCZ Habitat Features of Conservation Importance June 2021"
WALES = "Environment (Wales) Act Section 7 and OSPAR: Marine Habitats July 2020"
EOV_SG = "Essential Ocean Variables in Europe - seagrass cover (polygons, v2019)"
GEOLOGY = "EMODnet Geology seabed substrate (draft) July 2021"
NONE = "none"

# (table, type, data source, spatial scope, query, result, note); queries as printed (straight quotes)
RULES = [
    ("6", "biogenic substrate", EUNIS07, "", "HAB_TYPE = 'A5.6' (Sublittoral biogenic reefs) OR HAB_TYPE = 'A6.6' (Deep sea bioherms)", "y", ""),
    ("6", "Ostrea edulis beds", OSPAR20, "", "HabType = 'Ostrea edulis beds'", "y", ""),
    ("6", "Hiatella arctica beds", EUNIS07, "", "HAB_TYPE = 'A5.626' (Hiatella arctica beds on silty clay with small pebbles and shells)", "n", ""),
    ("6", "Limaria hians beds", GEMS, "within the UK EEZ", "PMF = 'Flame shell beds'", "y", ""),
    ("6", "Limaria hians beds", EUNIS07, "outside the UK EEZ", "HAB_TYPE = 'A5.434' (Limaria hians beds in tide-swept sublittoral muddy mixed sediment)", "n", ""),
    ("6", "mussel beds", EUNIS07, "", "HAB_TYPE = 'A5.62' (Sublittoral mussel beds on sediment)", "y", ""),
    ("6", "Modiolus modiolus beds", OSPAR20, "", "HabType = 'Modiolous modiolus Horse mussel beds'", "y", "'Modiolous' as printed"),
    ("6", "Mytilus edulis beds", GEMS, "within the Scottish part of the UK EEZ", "PMF = 'Blue mussel beds'", "y", ""),
    ("6", "Mytilus edulis beds", NE_FOCI, "within the English part of the UK EEZ", "FOCI_name = 'Blue Mussel beds' OR FOCI_name = 'Blue Mussel Beds' OR FOCI_name = 'Blue Mussel (Mytilus edulis) beds'", "y", ""),
    ("6", "Mytilus edulis beds", WALES, "within the Welsh part of the UK EEZ", "\"layer_id\" = 'CCW_Blue_Mussel_Beds_01' AND \"zone\" <> 'Intertidal'", "n", ""),
    ("6", "Mytilus edulis beds", EUNIS07, "outside the Scottish, English and Welsh parts of the UK EEZ", "HAB_TYPE = 'A5.625' (Mytilus edulis beds on sublittoral sediment)", "y", ""),
    ("6", "worm reefs", EUNIS07, "", "HAB_TYPE = 'A5.61' (Sublittoral polychaete worm reefs on sediment)", "y", ""),
    ("6", "Sabellaria alveolata reefs", NE_FOCI, "within the English part of the UK EEZ", "\"FOCI_name\" = 'Honeycomb worm (Sabellaria alveolata) reefs' OR \"FOCI_name\" = 'Sabellaria alveolata reefs'", "y", "'=' missing after the first FOCI_name in the report"),
    ("6", "Sabellaria alveolata reefs", WALES, "within the Welsh part of the UK EEZ", "\"Habitat_na\" = 'Honeycomb worm (Sabellaria alveolata) reefs' AND \"zone\" <> 'Intertidal'", "n", ""),
    ("6", "Sabellaria alveolata reefs", EUNIS07, "outside the English and Welsh parts of the UK EEZ", "HAB_TYPE = 'A5.612' (Sabellaria alveolata on variable salinity sublittoral mixed sediment)", "n", ""),
    ("6", "Sabellaria spinulosa reefs", OSPAR20, "", "HabType = 'Sabellaria spinulosa reefs'", "y", ""),
    ("6", "Serpula vermicularis reefs", GEMS, "within the UK EEZ", "PMF = 'Serpulid aggregations'", "y", ""),
    ("6", "Serpula vermicularis reefs", EUNIS07, "outside the UK EEZ", "HAB_TYPE = 'A5.613' (Serpula vermicularis reefs on very sheltered circalittoral muddy sand)", "n", ""),
    ("6", "cold water coral reefs", EUNIS07, "", "HAB_TYPE = 'A5.63' (Circalittoral coral reefs)", "n", ""),
    ("6", "Desmophyllum pertusum (Lophelia pertusa) reefs", OSPAR20, "", "HabType = 'Lophelia pertusa reefs'", "y", ""),
    ("6", "Madrepora oculata reefs", NONE, "", "", "n", "no known sources of polygon data: EUNIS 2007-11 has no Madrepora oculata reef biotopes"),
    ("6", "Solenosmilia variabilis reefs", NONE, "", "", "n", "no known sources of polygon data: EUNIS 2007-11 has no Solenosmilia variabilis reef biotopes (EUNIS 2019 does)"),
    ("7", "biogenic substrate", EUNIS07, "", "HAB_TYPE = 'A5.6' (Sublittoral biogenic reefs) OR HAB_TYPE = 'A6.6' (Deep sea bioherms)", "n", ""),
    ("7", "Posidonia oceanica meadows", ANNEX, "", "Annex I feature = '1120'", "y", ""),
    ("7", "Posidonia oceanica meadows", EUNIS07, "", "HAB_TYPE = 'A5.535'", "y", ""),
    ("7", "Posidonia oceanica meadows", EOV_SG, "", "eunis_code = 'A5.535'", "y", ""),
    ("7", "Posidonia oceanica meadows", GEOLOGY, "", "Surface_feature = 'Posidonia meadow' OR Surface_feature = 'Posidonia meadow ; Bio-lithoclastic sediment (50%<CaCO3<75%)' OR (Surface_feature = 'Seagrass meadow' AND 'comments' contains 'posidonia oceanica')", "y", ""),
    ("7", "live Posidonia oceanica meadows", EOV_SG, "", "\"eunis_code\" = 'A5.5351' OR \"eunis_code\" = 'A5.5354'", "n", ""),
    ("7", "live Posidonia oceanica meadows", EUNIS07, "", "HAB_TYPE = 'A5.5351' OR HAB_TYPE = 'A5.5354'", "n", ""),
    ("7", "dead mattes of Posidonia oceanica", EUNIS07, "", "HAB_TYPE = 'A5.5353'", "y", ""),
    ("7", "dead mattes of Posidonia oceanica", EOV_SG, "", "\"eunis_code\" = 'A5.5353'", "y", ""),
    ("7", "dead mattes of Posidonia oceanica", GEOLOGY, "", "Surface_feature = 'Seagrass matte (degraded)'", "y", ""),
    ("7", 'Posidonia oceanica "Barrier-reef"', EUNIS07, "", "HAB_TYPE = 'A5.5352'", "n", ""),
    ("7", 'Posidonia oceanica "Barrier-reef"', EOV_SG, "", "Habitat subtype = 'Posidonia oceanica \"Barrier-reef\"'", "n", ""),
    ("7", "Sabellaria alveolata reefs", EUNIS07, "", "HAB_TYPE = 'A5.612' (Sabellaria alveolata on variable salinity sublittoral mixed sediment)", "miscoded", "a polygon was returned but on further inspection it appears to have been miscoded"),
    ("7", "coralligenous platforms", EUNIS07, "", "HAB_TYPE = 'A4.26D'", "y", ""),
    ("7", "Madrepora oculata reefs", NONE, "", "", "n", "no known sources of polygon data: EUNIS 2007-11 has no Madrepora oculata reef biotopes"),
    ("7", "Facies with Vermetus of the infralittoral algae biocenosis", NONE, "", "", "not applicable", "very limited extension in the Mediterranean: can only be represented by points or lines"),
    ("7", "Facies with Ficopomatus enigmaticus of the euryhaline and/or eurythermal lagoon biocenosis", EUNIS07, "", "HAB_TYPE = 'A5.529' (Facies with Ficopomatus enigmaticus)", "y", ""),
    ("8", "biogenic substrate", ANNEX, "", "Annex I = '1170' (Reefs) AND subtype = 'Biogenic concretions'", "y", ""),
    ("8", "bivalve reefs", HUB, "", "ORIG_HAB is one of 'A[A or B].[A, B, E, H, I, J or M]1E' (Baltic [photic or aphotic] [various substrates] dominated by bivalves), e.g. AA.A1E, AB.E1E, etc.", "n", ""),
    ("8", "mussel beds", HUB, "", "ORIG_HAB is one of 'A[A or B].[A, B, E, H, I, J or M]1E1' (Baltic [photic or aphotic] [various substrates] dominated by Mytilidae), e.g. AA.A1E1, AB.E1E1, etc.", "n", ""),
    ("8", "dominated by zebra mussel", HUB, "", "ORIG_HAB = 'AA.A1E2' OR ORIG_HAB = 'AA.H1E2' OR ORIG_HAB = 'AA.M1E2'", "n", ""),
    ("8", "dominated by valve snails", HUB, "", "ORIG_HAB = 'AA.H1E3' (Baltic photic muddy sediment dominated by valve snails (Valvata spp.))", "n", ""),
    ("8", "shell gravel", HUB, "", "ORIG_HAB contains 'AA.E*' (Baltic photic shell gravel), except AA.E1E and AA.E1E1 OR ORIG_HAB contains 'AB.E*' (Baltic aphotic shell gravel), AB.E1E and AB.E1E1", "n", ""),
    ("8", "worm reefs", HUB, "", "ORIG_HAB = 'AA.H1K' OR ORIG_HAB = 'AB.H1K'", "n", ""),
    ("8", "peat bottoms", NONE, "", "", "n", "no known sources of polygons for this habitat"),
    ("9", "biogenic substrate", EUNIS07, "", "HAB_TYPE = 'A5.6' (Sublittoral biogenic reefs) OR HAB_TYPE = 'A6.6' (Deep sea bioherms)", "n", ""),
    ("9", "Ostrea edulis beds", EUNIS07, "", "HAB_TYPE = 'A5.64' (Pontic Ostrea edulis biogenic reefs on mobile seabottom)", "n", ""),
    ("9", "mussel beds", EUNIS07, "", "HAB_TYPE = 'A5.62' (Sublittoral mussel beds on sediment)", "n", ""),
    ("9", "worm reefs", EUNIS07, "", "HAB_TYPE = 'A5.61' (Sublittoral polychaete worm reefs on sediment)", "n", ""),
]
_RULE_REGION = {"6": ATL, "7": MED, "8": BAL, "9": BLS}
# UK lists queried by name: crosswalks to the systems used by the JNCC correlation tables
UK_LIST_QUERIES = [("UK_PMF", "Flame shell beds", "Limaria hians beds"),
                   ("UK_PMF", "Blue mussel beds", "Mytilus edulis beds"),
                   ("UK_PMF", "Serpulid aggregations", "Serpula vermicularis reefs"),
                   ("UK_MCZ_FOCI", "Blue Mussel beds", "Mytilus edulis beds"),
                   ("UK_MCZ_FOCI", "Honeycomb worm (Sabellaria alveolata) reefs", "Sabellaria alveolata reefs"),
                   ("UK_MCZ_FOCI", "Sabellaria alveolata reefs", "Sabellaria alveolata reefs")]


def extraction_rules() -> pd.DataFrame:
    rows = [{"composite": "EMODNET_BIOGENIC_2021", "region": _RULE_REGION[t], "target_system": "EMODNET_BIOGENIC_2021",
             "target_code": type_code(typ), "data_source": ds, "spatial_scope": scope, "query": q, "result": res,
             "source": SRC + f", Table {t}", "notes": note} for t, typ, ds, scope, q, res, note in RULES]
    return pd.DataFrame(rows, columns=EXTRACTION_RULES_COLUMNS)


def crosswalk_uk_lists() -> pd.DataFrame:
    rows = [{"from_system": sys_, "from_code": slug(name), "to_system": "EMODNET_BIOGENIC_2021", "to_code": type_code(t),
             "relationship": "maps to", "source": SRC + ", Table 6 (query strings)",
             "notes": f"region: {ATL}; name in query: {name}"} for sys_, name, t in UK_LIST_QUERIES]
    return pd.DataFrame(rows, columns=CROSSWALKS_COLUMNS).drop_duplicates(["from_system", "from_code", "to_code"])
