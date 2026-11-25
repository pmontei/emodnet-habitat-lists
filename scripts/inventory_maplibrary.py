"""Inventory of the EMODnet Seabed Habitats map library (habitat maps in DEF format).

Reads only the attribute tables (``.dbf``) of the shapefiles in a folder: no geometry, no GIS
library (Python standard library only), so it runs on any machine.

Usage::

    python scripts/inventory_maplibrary.py <folder with the shapefiles> <output folder> \
        [--filter data/processed/eov_seagrass_filter.csv]

Outputs (CSV, UTF-8):

``maps.csv``
    One row per map: file, GUI, number of polygons, fields, distinct ORIG_CLASS and HAB_CLASS
    values, and, with ``--filter``, the number of candidate polygons for the product.
``class_values.csv``
    Distinct values of ORIG_CLASS and HAB_CLASS with the number of maps and polygons: the input of
    the ``class_aliases`` table (classification name used in the maps -> ``system``).
``habitat_values.csv``
    Distinct (map, field pair, class, code) combinations with their number of polygons, for
    ``HAB_CLASS`` + ``HAB_TYPE`` and ``ORIG_CLASS`` + ``ORIG_HAB``.
``candidates.csv`` (with ``--filter``)
    The combinations of ``habitat_values.csv`` that look like members of the product: the code is
    a code of the filter (any classification, ``use`` = yes / partial / broader), or the text names
    seagrass. Preliminary: the classification of each code is checked only once ``class_aliases``
    exists, because EUNIS 2019 / 2022 codes were re-used with other meanings.
"""

from __future__ import annotations

import argparse
import csv
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = ("GUI", "ORIG_HAB", "ORIG_CLASS", "HAB_TYPE", "HAB_CLASS", "T_RELATE", "SUM_CONF")
SEAGRASS = re.compile(
    r"zostera|posidoni|cymodoce|halophila|ruppia|zannichellia|thalassia|syringodium|halodule|sea-?grass|"
    r"eel-?grass|herbier|pradera|fanerógam|fanerogam|angiosperm|phanerogam|seegras|zeegras|ålegräs|ålegræs|"
    r"meriajok", re.I)


def read_dbf(path: Path, wanted=FIELDS):
    """Yield dicts with the ``wanted`` fields of a dBase III file (case-insensitive field names)."""
    cpg = path.with_suffix(".cpg")
    if not cpg.exists():
        cpg = path.with_suffix(".CPG")
    enc = "utf-8"
    if cpg.exists():
        c = cpg.read_text(errors="ignore").strip().lower()
        enc = {"utf-8": "utf-8", "utf8": "utf-8", "65001": "utf-8"}.get(c, c or "utf-8")
    with open(path, "rb") as f:
        head = f.read(32)
        n, header_len, rec_len = struct.unpack("<IHH", head[4:12])
        fields, off = [], 1
        while True:
            d = f.read(32)
            if not d or d[0] == 0x0D:
                break
            name = d[:11].split(b"\0")[0].decode("latin-1").upper()
            length = d[16]
            fields.append((name, off, length))
            off += length
        want = [(nm, o, ln) for nm, o, ln in fields if nm in wanted]
        f.seek(header_len)
        for _ in range(n):
            rec = f.read(rec_len)
            if len(rec) < rec_len:
                break
            if rec[:1] == b"*":   # deleted record
                continue
            row = {}
            for nm, o, ln in want:
                raw = rec[o:o + ln]
                try:
                    v = raw.decode(enc)
                except (UnicodeDecodeError, LookupError):
                    v = raw.decode("latin-1")
                row[nm] = v.strip()
            yield row
    return [nm for nm, _, _ in fields]


def dbf_fields(path: Path) -> list[str]:
    with open(path, "rb") as f:
        f.read(32)
        out = []
        while True:
            d = f.read(32)
            if not d or d[0] == 0x0D:
                break
            out.append(d[:11].split(b"\0")[0].decode("latin-1").upper())
    return out


def load_filter(path: Path) -> dict[str, str]:
    """code -> best use (yes > partial > broader) over all classifications of the filter."""
    order = {"yes": 0, "partial": 1, "broader": 2}
    best: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["use"] not in order:
                continue
            for code in {r["code"], r["code"].replace(".", "")}:
                if code not in best or order[r["use"]] < order[best[code]]:
                    best[code] = r["use"]
    return best


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--filter", type=Path, help="eov_seagrass_filter.csv (or another product filter)")
    a = p.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    flt = load_filter(a.filter) if a.filter else None

    class_maps: dict[tuple[str, str], set] = defaultdict(set)
    class_n: Counter = Counter()
    maps_rows, hab_rows = [], []
    files = sorted(a.folder.glob("*.dbf")) + sorted(a.folder.glob("*.DBF"))
    for i, dbf in enumerate(files, 1):
        fields = dbf_fields(dbf)
        combos: Counter = Counter()
        guis, n, n_cand = set(), 0, 0
        for r in read_dbf(dbf):
            n += 1
            guis.add(r.get("GUI", ""))
            hc, ht = r.get("HAB_CLASS", ""), r.get("HAB_TYPE", "")
            oc, oh = r.get("ORIG_CLASS", ""), r.get("ORIG_HAB", "")
            combos[("HAB", hc, ht)] += 1
            combos[("ORIG", oc, oh)] += 1
            if flt is not None and (ht in flt or oh in flt or SEAGRASS.search(oh) or SEAGRASS.search(ht)):
                n_cand += 1
        gui = ";".join(sorted(g for g in guis if g)) or dbf.stem
        for (kind, cls, code), k in combos.items():
            fld = "HAB_CLASS" if kind == "HAB" else "ORIG_CLASS"
            class_maps[(fld, cls)].add(dbf.stem)
            class_n[(fld, cls)] += k
            hab_rows.append({"file": dbf.stem, "GUI": gui, "pair": f"{fld}+{'HAB_TYPE' if kind == 'HAB' else 'ORIG_HAB'}",
                             "class": cls, "code": code, "n_polygons": k})
        maps_rows.append({
            "file": dbf.stem, "GUI": gui, "n_polygons": n,
            "orig_class": " | ".join(sorted({c for (kd, c, _) in combos if kd == "ORIG"})),
            "hab_class": " | ".join(sorted({c for (kd, c, _) in combos if kd == "HAB"})),
            "n_hab_type": len({h for (kd, _, h) in combos if kd == "HAB"}),
            "n_candidates": n_cand if flt is not None else "",
            "fields": " ".join(fields)})
        if i % 50 == 0:
            print(f"{i}/{len(files)} maps", file=sys.stderr)

    def write(name, rows, cols):
        with open(a.out / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)

    write("maps.csv", maps_rows, list(maps_rows[0]) if maps_rows else ["file"])
    write("class_values.csv",
          [{"field": fld, "value": cls, "n_maps": len(class_maps[(fld, cls)]), "n_polygons": class_n[(fld, cls)]}
           for fld, cls in sorted(class_n, key=lambda k: (k[0], -class_n[k]))],
          ["field", "value", "n_maps", "n_polygons"])
    write("habitat_values.csv", hab_rows, ["file", "GUI", "pair", "class", "code", "n_polygons"])
    if flt is not None:
        cand = []
        for r in hab_rows:
            code = r["code"]
            use = flt.get(code) or flt.get(code.replace(".", ""))
            if use or SEAGRASS.search(code):
                cand.append({**r, "match": f"code ({use})" if use else "text"})
        write("candidates.csv", cand, ["file", "GUI", "pair", "class", "code", "n_polygons", "match"])
    print(f"{len(files)} maps, {sum(r['n_polygons'] for r in maps_rows)} polygons -> {a.out}")


if __name__ == "__main__":
    main()
