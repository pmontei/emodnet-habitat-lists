"""Build an EOV polygon composite from the EMODnet map library (test version, D3.03).

Steps (``--steps``, default all):

``select``
    For each map (shapefiles in DEF format), select the polygons of the wanted items of a product
    filter (``eov_seagrass_filter.csv``, ``use = yes``):

    * ``HAB_TYPE`` code of the filter for the classification named in ``HAB_CLASS``;
    * ``ORIG_HAB`` code of the filter for the classification named in ``ORIG_CLASS``;
    * or ``ORIG_HAB`` / ``HAB_TYPE`` text naming the item (e.g. "posidoni" for Posidonia beds).

    Polygons whose code is excluded for the item (``use = no``), or whose text names an excluded
    association (e.g. *Caulerpa prolifera*), are left out. The classification names of the maps are
    translated with ``CLASS_ALIASES`` (provisional ``class_aliases``). Geometries are reprojected to
    EPSG:3035, repaired (``make_valid``) and snapped to the INSPIRE 1 m grid (``set_precision(1.0)``,
    the INSPIRE grid has its origin at 0, 0), and written to ``selected/<map>.fgb``. Resumable
    (``select_done.txt``) and with ``--time-limit``, for machines that stop long jobs.
``resolve``
    Overlaps are resolved tile by tile (INSPIRE 10 km cells generated with ``standardgrid``): each
    polygon keeps only the part not covered by a polygon of higher rank. Rank: source priority
    (D3.11 2025, Table 3: OSPAR 1, Annex I maps 2, EUNIS maps 3, other maps 4), then ``SUM_CONF``
    (higher first), then determination date (more recent first). Output: ``composite.gpkg``, layer
    ``polygons``, in the EOV polygon template (D3.11 2025, Appendix Table 1) plus provenance fields.
``grid``
    Cover of the composite in INSPIRE 1 km cells (layer ``inspire_1km``: area and percentage).
``compare``
    Area by map compared with the 2025 composite (``--old``), for the same items.

Usage (test with Posidonia beds only)::

    python scripts/composite_eov.py --maps Dados/EMODnetSBH_EUNIS_surveymaps --out Dados/composites_test/posidonia \
        --filter Scripts/EOV_seagrass/eov_seagrass_filter.csv --habitats Scripts/EOV_seagrass/habitats.csv \
        --items posidonia-beds --old Dados/OLD_composites/SeagrassBeds_EOV_2025/seagrass_polygons_2025.shp

Needs geopandas (>= 1.0), shapely (>= 2.0), pyogrio and standardgrid.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from shapely import STRtree, box

CRS = "EPSG:3035"
TILE = 10_000      # INSPIRE 10 km tiles for processing
CELL = 1_000       # INSPIRE 1 km cells for the cover grid
PRECISION = 1.0    # INSPIRE 1 m grid

# provisional class_aliases: classification name used in the maps -> system of the repository
CLASS_ALIASES = {
    "eunis (version 2007-11)": "EUNIS_2012", "eunis version 2007-11": "EUNIS_2012", "eunis 2007-11": "EUNIS_2012",
    "eunis (version 2022)": "EUNIS_M_2022", "eunis version 2022": "EUNIS_M_2022",
    "eunis (version 2019)": "EUNIS_M_2019", "eunis version 2019": "EUNIS_M_2019",
    "habitats directive annex i habitats": "ANNEX_I", "habitats directive": "ANNEX_I",
    "typologie des biocenoses de mediterranee": "BARCELONA_2006",
    "typologie des biocenoses benthiques de mediterranee": "BARCELONA_2006",
    "benthic biocenoses of mediterranean sea": "BARCELONA_2006",
    "national typology of mediterranean benthic biocenoses": "BARCELONA_2006",
}
# item -> (text naming the item, text naming an excluded association)
ITEM_TEXT = {
    "posidonia-beds": (r"posidoni", r"caulerpa prolifera"),
    "cymodocea-beds": (r"cymodoce", r"$^"),
    "zostera-beds": (r"zostera|eel-?grass", r"$^"),
    "halophila-beds": (r"(?<!iris )halophila", r"$^"),
    "ruppia-beds": (r"ruppia", r"$^"),
}
EUNIS_VERSION = {"EUNIS_2012": "2007-11", "EUNIS_M_2019": "2019", "EUNIS_M_2022": "2022"}
ANNEX_I_OF_ITEM = {"posidonia-beds": ("1120", "Posidonia beds (Posidonion oceanicae)")}
DEF_COLS = ["GUI", "POLYGON", "ORIG_HAB", "ORIG_CLASS", "HAB_TYPE", "HAB_CLASS", "DET_NAME", "DET_DATE",
            "COMP", "COMP_TYPE", "SUM_CONF"]
TOKEN = re.compile(r"[A-Z]{1,3}\d?[\d.]*\d|[IVX]+(?:\.\d+)+|\d{4}")


def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def alias(value: str) -> str:
    return CLASS_ALIASES.get(" ".join(str(value).lower().split()), "")


def load_filter(path: Path, items: list[str]):
    """(codes kept, codes excluded) as {system: set(codes)} for the items."""
    keep: dict[str, set] = {}
    drop: dict[str, set] = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["item"] not in items:
                continue
            target = keep if r["use"] == "yes" else drop if r["use"] == "no" else None
            if target is not None:
                target.setdefault(r["system"], set()).add(r["code"])
    return keep, drop


def codes_in(text: str) -> list[str]:
    """Codes in a field value: 'A5.535', 'A5.535/A5.53', 'III.5.1.b. - Biocenose...' -> 'III.5.1'."""
    return [t.rstrip(".") for t in TOKEN.findall(str(text))]


def match_rows(df: pd.DataFrame, keep, drop, item_re, excl_re) -> tuple[np.ndarray, list[str]]:
    """Boolean mask of the polygons to keep and the rule that matched each one."""
    rules = []
    for hc, ht, oc, oh in zip(df.HAB_CLASS, df.HAB_TYPE, df.ORIG_CLASS, df.ORIG_HAB):
        hs, os_ = alias(hc), alias(oc)
        hcodes, ocodes = codes_in(ht), codes_in(oh)
        if any(c in drop.get(hs, ()) for c in hcodes) or any(c in drop.get(os_, ()) for c in ocodes) or \
                re.search(excl_re, f"{oh} {ht}", re.I):
            rules.append("")
        elif any(c in keep.get(hs, ()) for c in hcodes):
            rules.append("HAB_TYPE code")
        elif any(c in keep.get(os_, ()) for c in ocodes):
            rules.append("ORIG_HAB code")
        elif re.search(item_re, f"{oh} {ht}", re.I):
            rules.append("text")
        else:
            rules.append("")
    return np.array([bool(r) for r in rules]), rules


def polygons_only(geoms) -> np.ndarray:
    """Polygons of each geometry, as one (Multi)Polygon per input: lines and points left by an
    intersection or a difference (GeometryCollection) are dropped, never the polygons."""
    out = []
    for g in geoms:
        parts = [p for p in shapely.get_parts(shapely.get_parts(g)) if shapely.get_type_id(p) == 3]
        out.append(shapely.multipolygons(parts) if len(parts) > 1 else parts[0] if parts else
                   shapely.Polygon())
    return np.array(out, dtype=object)


def year(value) -> int:
    m = re.search(r"(19|20)\d{2}", str(value))
    return int(m.group(0)) if m else 0


def step_select(a, keep, drop, names) -> None:
    """One FlatGeobuf per map in ``out/selected/`` (resumable: maps listed in ``select_done.txt`` are
    skipped; ``--time-limit`` stops after that many seconds, run again to continue)."""
    sel_dir = a.out / "selected"
    sel_dir.mkdir(exist_ok=True)
    done_file = a.out / "select_done.txt"
    done = set(done_file.read_text().split()) if done_file.exists() else set()
    t_start = time.time()
    item = a.items[0]
    item_re = "|".join(ITEM_TEXT[i][0] for i in a.items)
    excl_re = "|".join(ITEM_TEXT[i][1] for i in a.items)
    files = sorted(a.maps.glob("*.shp"))
    if a.only:
        wanted = set(Path(a.only).read_text().split())
        files = [f for f in files if f.stem in wanted]
    n_total, rows_maps = 0, []
    for i, shp in enumerate(files, 1):
        if shp.stem in done:
            continue
        if a.time_limit and time.time() - t_start > a.time_limit:
            log(f"select paused at {len(done)}/{len(files)} maps (time limit); run again to continue")
            return
        try:
            info = pyogrio.read_info(shp)["fields"]
            cols = [f for f in info if f.upper() in DEF_COLS]
            attrs = pyogrio.read_dataframe(shp, read_geometry=False, columns=cols)
        except Exception as e:  # noqa: BLE001
            log(f"skip {shp.name}: {e}")
            continue
        attrs.columns = [c.upper() for c in attrs.columns]
        for c in DEF_COLS:
            if c not in attrs:
                attrs[c] = ""
        attrs = attrs.fillna("").astype(str)
        mask, rules = match_rows(attrs, keep, drop, item_re, excl_re)
        if not mask.any():
            _done(done_file, done, shp.stem)
            continue
        fids = np.flatnonzero(mask)
        g = pyogrio.read_dataframe(shp, fids=fids, columns=cols)
        g = g.rename(columns={c: c.upper() for c in g.columns if c != "geometry"})
        for c in DEF_COLS:
            if c not in g:
                g[c] = ""
        g[DEF_COLS] = g[DEF_COLS].fillna("").astype(str)
        g["Match_rule"] = [rules[j] for j in fids]
        if g.crs is None:
            g = g.set_crs("EPSG:4326")
        g = g.to_crs(CRS)
        g["geometry"] = polygons_only(shapely.set_precision(shapely.make_valid(shapely.force_2d(g.geometry.values)),
                                                            PRECISION))
        g = g.explode(index_parts=False)
        g = g[g.geometry.geom_type.isin(["Polygon", "MultiPolygon"]) & ~g.geometry.is_empty]
        g = g[g.geometry.area >= 1.0]
        if g.empty:
            _done(done_file, done, shp.stem)
            continue
        hs = g.HAB_CLASS.map(alias)
        hab_code = [next((c for c in codes_in(t) if c in keep.get(s, ())), "") for t, s in zip(g.HAB_TYPE, hs)]
        out_df = gpd.GeoDataFrame({
            "Map_id": g.GUI.astype(str), "Polygon": g.POLYGON.astype(str), "Hab_origin": g.ORIG_HAB.astype(str),
            "Orig_class": g.ORIG_CLASS.astype(str), "Eunis_code": g.HAB_TYPE.astype(str),
            "Hab_class": g.HAB_CLASS.astype(str), "Eunis_ver": hs.map(EUNIS_VERSION).fillna(""),
            "Eunis_name": [names.get((s, c), "") for s, c in zip(hs, hab_code)],
            "Anxi_code": ANNEX_I_OF_ITEM.get(item, ("", ""))[0], "Anxi_name": ANNEX_I_OF_ITEM.get(item, ("", ""))[1],
            "Ai_subtype": "", "Ospar_hab": "", "determiner": g.DET_NAME.astype(str), "Det_date": g.DET_DATE.astype(str),
            "Source": "EMODnet Seabed Habitats map library (" + g.GUI.astype(str) + ")",
            "Item": item, "Match_rule": g.Match_rule, "Comp": g.COMP.astype(str), "Comp_type": g.COMP_TYPE.astype(str),
            "Sum_conf": pd.to_numeric(g.SUM_CONF, errors="coerce").fillna(-1).astype(int),
            "Priority": np.where(hs == "ANNEX_I", 2, np.where(hs.str.startswith("EUNIS"), 3, 4)),
            "Year": [year(d) for d in g.DET_DATE],
        }, geometry=g.geometry.values, crs=CRS)
        pyogrio.write_dataframe(out_df, sel_dir / f"{shp.stem}.fgb", driver="FlatGeobuf")
        n_total += len(out_df)
        row = {"file": shp.stem, "n_selected": len(out_df), "area_km2": round(out_df.area.sum() / 1e6, 4),
               **{r: int((out_df.Match_rule == r).sum()) for r in ["HAB_TYPE code", "ORIG_HAB code", "text"]}}
        by_map = a.out / "selected_by_map.csv"
        pd.DataFrame([row]).to_csv(by_map, mode="a", header=not by_map.exists(), index=False)
        _done(done_file, done, shp.stem)
        log(f"select {i}/{len(files)} {shp.stem}: {len(out_df)} polygons")
    log(f"select done: {len(done)}/{len(files)} maps -> {sel_dir}")


def _done(done_file: Path, done: set, stem: str) -> None:
    done.add(stem)
    with open(done_file, "a") as f:
        f.write(stem + "\n")


def tiles_for(bounds, size) -> gpd.GeoDataFrame:
    """INSPIRE cells of ``size`` m covering ``bounds`` (centroids from standardgrid)."""
    from standardgrid import Grid
    pts = Grid(standard="inspire", resolution=float(size)).generate(tuple(bounds), bbox_crs=CRS).points
    xc, yc = pts.iloc[:, 0].to_numpy(), pts.iloc[:, 1].to_numpy()
    h = size / 2
    code = [f"CRS3035RES{int(size) if size >= 1000 else size}mN{int(y - h)}E{int(x - h)}" for x, y in zip(xc, yc)]
    if size >= 1000:
        code = [f"CRS3035RES{int(size / 1000)}kmN{int((y - h) / 1000)}E{int((x - h) / 1000)}" for x, y in zip(xc, yc)]
    return gpd.GeoDataFrame({"cell": code}, geometry=shapely.box(xc - h, yc - h, xc + h, yc + h), crs=CRS)


MAX_PER_TILE = 2000   # above this, a 10 km tile is processed by its 1 km cells


def resolve_cell(geoms, idx, cell) -> tuple[list, list]:
    """Pieces of ``geoms[idx]`` inside ``cell`` without overlaps: each part loses what the parts of
    higher rank (earlier in ``idx``, which is sorted by rank) cover. Only the parts that touch it
    are used, so the cost grows with the local overlaps, not with the cell."""
    parts = shapely.intersection(geoms[idx], cell)
    ok = ~shapely.is_empty(parts)
    idx, parts = idx[ok], parts[ok]
    if not len(parts):
        return [], []
    shapely.prepare(parts)
    left, right = STRtree(parts).query(parts, predicate="intersects")
    higher = left > right            # right has a higher rank than left
    by_part: dict[int, list[int]] = {}
    for l, r in zip(left[higher], right[higher]):
        by_part.setdefault(int(l), []).append(int(r))
    kept_geom, kept_idx = [], []
    for i_part, (j, gpart) in enumerate(zip(idx, parts)):
        over = by_part.get(i_part)
        if over:
            hs = parts[over]
            if shapely.covers(hs, gpart).any():   # fully covered by a higher rank: dropped
                continue
            try:   # clip the higher-rank parts to the extent of this part before the difference
                clipped = shapely.intersection(hs, box(*gpart.bounds))
                piece = shapely.difference(gpart, shapely.union_all(clipped))
            except shapely.errors.GEOSException:
                piece = shapely.difference(gpart, shapely.union_all(shapely.make_valid(hs)))
        else:
            piece = gpart
        piece = polygons_only([shapely.set_precision(shapely.make_valid(piece), PRECISION)])[0]
        if piece.is_empty or piece.area < 1.0:
            continue
        kept_geom.append(piece)
        kept_idx.append(int(j))
    return kept_geom, kept_idx


def step_resolve(a) -> None:
    files = [f for f in sorted((a.out / "selected").glob("*.fgb")) if not f.stem.endswith("_temp")]
    sel = pd.concat([pyogrio.read_dataframe(f) for f in files], ignore_index=True)
    sel = gpd.GeoDataFrame(sel, geometry="geometry", crs=CRS)
    log(f"resolve: {len(sel)} polygons")
    sel = sel.sort_values(["Priority", "Sum_conf", "Year", "Map_id", "Polygon"],
                          ascending=[True, False, False, True, True]).reset_index(drop=True)
    sel["rank"] = np.arange(len(sel))
    tree = STRtree(sel.geometry.values)
    tiles = tiles_for(sel.total_bounds, TILE)
    tiles = tiles[[len(tree.query(t)) > 0 for t in tiles.geometry.values]].reset_index(drop=True)
    log(f"{len(tiles)} INSPIRE 10 km tiles with data")
    out = a.out / "composite.gpkg"
    if out.exists():
        out.unlink()
    geoms = sel.geometry.values
    n_out, t0 = 0, time.time()
    for k, (cell, tile) in enumerate(zip(tiles.cell, tiles.geometry.values), 1):
        idx = np.sort(tree.query(tile, predicate="intersects"))   # sorted = by rank
        if not len(idx):
            continue
        # dense tiles are processed by their INSPIRE 1 km cells (memory and time stay bounded)
        cells = [(tile, idx)]
        if len(idx) > MAX_PER_TILE:
            sub = tiles_for(tile.bounds, CELL)
            sub = sub[shapely.within(sub.geometry.values, shapely.buffer(tile, 1))]
            cells = [(c, np.sort(tree.query(c, predicate="intersects"))) for c in sub.geometry.values]
        kept_geom, kept_idx = [], []
        for cgeom, cidx in cells:
            if len(cidx):
                g_, i_ = resolve_cell(geoms, cidx, cgeom)
                kept_geom += g_
                kept_idx += i_
        if not kept_idx:
            continue
        part = sel.iloc[kept_idx].drop(columns="geometry").copy()
        part["Inspire10k"] = cell
        g = gpd.GeoDataFrame(part, geometry=kept_geom, crs=CRS).explode(index_parts=False)
        g = g[g.geometry.geom_type == "Polygon"]
        g = g[g.area >= 1.0]
        pyogrio.write_dataframe(g.drop(columns=["rank"]), out, layer="polygons", append=out.exists())
        n_out += len(g)
        if k % 50 == 0 or len(idx) > MAX_PER_TILE:
            log(f"resolve {k}/{len(tiles)} tiles, {n_out} polygons, {time.time() - t0:.0f} s"
                + (f" ({cell}: {len(idx)} polygons, by 1 km cells)" if len(idx) > MAX_PER_TILE else ""))
    comp = pyogrio.read_dataframe(out, layer="polygons", read_geometry=False, columns=["Map_id"])
    log(f"resolve done: {len(comp)} polygons -> {out}")


def step_grid(a) -> None:
    comp = pyogrio.read_dataframe(a.out / "composite.gpkg", layer="polygons", columns=["Map_id", "Inspire10k"])
    tree = STRtree(comp.geometry.values)
    rows = []
    for cell10, g10 in comp.groupby("Inspire10k"):
        cells = tiles_for(g10.total_bounds, CELL)
        u = shapely.union_all(g10.geometry.values)
        inter = shapely.intersection(cells.geometry.values, u)
        area = shapely.area(inter)
        for c, cg, ar in zip(cells.cell, cells.geometry.values, area):
            if ar > 0:
                hit = g10.Map_id.values[g10.geometry.intersects(cg).values]
                rows.append({"cell": c, "area_m2": round(ar, 1), "cover_pct": round(100 * ar / CELL ** 2, 2),
                             "n_maps": len(set(hit)), "geometry": cg})
    grid = gpd.GeoDataFrame(rows, geometry="geometry", crs=CRS)
    grid = grid.drop_duplicates("cell")
    pyogrio.write_dataframe(grid, a.out / "composite.gpkg", layer="inspire_1km")
    log(f"grid done: {len(grid)} INSPIRE 1 km cells, {grid.area_m2.sum() / 1e6:.1f} km2")
    del tree


def step_compare(a, keep) -> None:
    new = pyogrio.read_dataframe(a.out / "composite.gpkg", layer="polygons", columns=["Map_id"])
    new_area = new.assign(a=new.area / 1e6).groupby("Map_id").a.sum()
    item_re = "|".join(ITEM_TEXT[i][0] for i in a.items)
    cols = ["map_id", "hab_origin", "eunis_code", "eunis_name", "anxi_code"]
    if a.old.is_dir():   # folder of FlatGeobuf parts (e.g. the 2025 polygons of the items, already extracted)
        parts = [f for f in sorted(a.old.glob("*.fgb")) if not f.stem.endswith("_temp")]
        old = gpd.GeoDataFrame(pd.concat([pyogrio.read_dataframe(f, columns=cols) for f in parts],
                                         ignore_index=True), geometry="geometry")
    else:
        old = pyogrio.read_dataframe(a.old, columns=cols)
    old = old[old.geometry.notna()].fillna("")
    codes = set().union(*keep.values())
    m = old.eunis_code.astype(str).isin(codes) | old.hab_origin.astype(str).str.contains(item_re, case=False) | \
        old.eunis_name.astype(str).str.contains(item_re, case=False) | \
        old.anxi_code.astype(str).isin({ANNEX_I_OF_ITEM.get(i, ("-",))[0] for i in a.items})
    old = old[m].to_crs(CRS)
    old_area = old.assign(a=old.area / 1e6).groupby("map_id").a.sum()
    cmp = pd.DataFrame({"area_km2_2026_test": new_area, "area_km2_2025": old_area}).fillna(0).round(3)
    cmp["diff_km2"] = (cmp.area_km2_2026_test - cmp.area_km2_2025).round(3)
    cmp.index.name = "Map_id"
    cmp.sort_values("area_km2_2026_test", ascending=False).to_csv(a.out / "compare_2025.csv")
    log(f"compare: test {new_area.sum():.1f} km2 in {len(new_area)} maps; 2025 {old_area.sum():.1f} km2 in "
        f"{len(old_area)} maps; only in 2025: {int((cmp.area_km2_2026_test == 0).sum())} maps, only in test: "
        f"{int((cmp.area_km2_2025 == 0).sum())} maps")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--maps", type=Path, required=True, help="folder with the map library shapefiles (DEF)")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--filter", type=Path, required=True, help="eov_seagrass_filter.csv")
    p.add_argument("--habitats", type=Path, required=True, help="habitats.csv of emodnet-habitat-lists")
    p.add_argument("--items", nargs="+", default=["posidonia-beds"])
    p.add_argument("--only", help="text file with the map file names to read (default: all)")
    p.add_argument("--old", type=Path, help="2025 composite polygons, for the comparison")
    p.add_argument("--steps", nargs="+", default=["select", "resolve", "grid", "compare"])
    p.add_argument("--time-limit", type=float, default=0, help="select: stop after this many seconds (resumable)")
    a = p.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    keep, drop = load_filter(a.filter, a.items)
    hab = pd.read_csv(a.habitats, dtype=str, keep_default_na=False, usecols=["system", "code", "name"])
    names = dict(zip(zip(hab.system, hab.code), hab.name))
    if "select" in a.steps:
        step_select(a, keep, drop, names)
    if "resolve" in a.steps:
        step_resolve(a)
    if "grid" in a.steps:
        step_grid(a)
    if "compare" in a.steps and a.old:
        step_compare(a, keep)


if __name__ == "__main__":
    sys.exit(main())
