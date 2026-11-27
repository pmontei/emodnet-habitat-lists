"""Build the Caribbean part of the EOV Seagrass polygon composite (D3.03), on the C-squares grid.

Inputs (folder ``--inputs``, one FlatGeobuf or shapefile per map, as prepared from
``Dados/Caribbean/Seagrass Cover/input data``; the file name starts with the group):

* ``IND__*``: individual habitat maps (only their seagrass polygons);
* ``TNC__*``: The Nature Conservancy habitat maps (Dense and Sparse Seagrass; WP3 decision 26/11/2026:
  used);
* ``ACA__*``: Allen Coral Atlas benthic maps, seagrass class (polygons of 100 m2 or more).

Priorities (EMODnet Seabed Habitats D3_03 Seagrass Data Selection Rules Caribbean):

1. surveys, transects, ROV, acoustic (MBES), snorkel / scuba: local studies (class I);
2. remote sensing, high resolution (< 5 m), local studies (class II);
3. remote sensing, high or medium resolution (< 10 m), regional studies (Nature Conservancy);
4. remote sensing, global studies (Allen Coral Atlas);
5. low resolution, regional or global (UNEP; not used here).

Within one priority the sub-classes of the rules (Ia before I before Ib, IIa before II before IIb, i.e.
higher resolution) come first (``Subprio``), then the more recent product (``Year``). Overlaps are
resolved with the noded overlay of ``composite_eov.py`` (each face goes to the polygon of highest
rank), tile by tile on the C-squares grid: 0.1 degree tiles (generated with ``standardgrid``), dense
tiles by their 0.01 degree cells. Vertices are snapped to the C-squares 0.00001 degree grid (about
1 m, origin 0, 0), the counterpart of the INSPIRE 1 m grid used for Europe. Polygons with the same
information are merged (dissolve); output in WGS84, with ``Area_km2`` computed in EPSG:6933
(equal area).

Steps (``--steps``): ``select``, ``resolve``, ``dissolve``, ``check``, ``export``, ``compare``.

Usage::

    python scripts/composite_caribbean.py --inputs carib_in --out seagrass_caribbean \\
        --old Dados/OLD_composites/SeagrassBeds_EOV_2025/seagrass_polygons_2025.shp
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from shapely import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from composite_eov import DISSOLVE_KEYS, log, make_valid, polygons_only, resolve_cell, year  # noqa: E402

CRS = "EPSG:4326"
AREA_CRS = "EPSG:6933"     # equal area, for Area_km2 and the summaries
PRECISION = 0.00001        # C-squares finest resolution (about 1 m)
MIN_AREA = PRECISION ** 2  # about 1.2 m2
TILE = 0.1                 # C-squares 0.1 degree tiles
CELL = 0.01                # C-squares 0.01 degree cells for dense tiles
MAX_PER_TILE = 2000
CHUNK = 40_000             # features read at a time (memory)

# GUI -> (priority, sub-priority, year of the product when the map has no date). D3_03 Caribbean rules.
INDIVIDUAL = {
    "PR004002": (1, 0, 2010), "PR004003": (1, 0, 2013),                       # Ia
    "AI004004": (1, 1, 2018), "FR004047": (1, 1, 2010), "MS004002": (1, 1, 2018),
    "VG004003": (1, 1, 2015), "VI005006": (1, 1, 2011),                       # I
    "PR004001": (1, 2, 2001),                                                 # Ib
    "FR004049": (2, 0, 2001),                                                 # IIa
    "AG004002": (2, 1, 2012), "AI004002": (2, 1, 2018), "VI004001": (2, 1, 2002),
    "VI004002": (2, 1, 2002), "VI004004": (2, 1, 2009),                       # II
    "FR004051": (2, 2, 0),                                                    # IIb
}
GROUPS = {"IND": "Individual habitat maps (Caribbean)", "TNC": "The Nature Conservancy habitat maps",
          "ACA": "Allen Coral Atlas benthic maps"}
GROUP_PRIORITY = {"TNC": 3, "ACA": 4}
ITEM = "tropical-seagrass-beds"


def csquare(lon: float, lat: float, res: float) -> str:
    """C-squares code of the cell of resolution ``res`` (10, 5, 1, 0.5, 0.1, 0.05, 0.01 ...) that
    contains the point (use the cell centre)."""
    q = 1 if lat >= 0 and lon >= 0 else 3 if lat < 0 <= lon else 5 if lat < 0 and lon < 0 else 7
    a, o = round(abs(lat) * 1e5), round(abs(lon) * 1e5)     # integer units of 0.00001 degree
    code = f"{q}{a // 1_000_000}{o // 1_000_000:02d}"
    a, o, size = a % 1_000_000, o % 1_000_000, 1_000_000
    while size / 2 >= res * 1e5 - 1e-9:
        sub = size // 10
        la, lo = a // sub, o // sub
        code += f":{1 + 2 * (la >= 5) + (lo >= 5)}"
        if size / 2 <= res * 1e5 + 1e-9:
            break
        code += f"{la}{lo}"
        if sub <= res * 1e5 + 1e-9:
            break
        a, o, size = a % sub, o % sub, sub
    return code


def tiles_for(bounds, size) -> gpd.GeoDataFrame:
    """C-squares cells of ``size`` degrees covering ``bounds`` (centres from standardgrid)."""
    from standardgrid import Grid
    pts = Grid(standard="csquares", resolution=float(size)).generate(tuple(bounds), bbox_crs=CRS).points
    xc, yc = pts.iloc[:, 0].to_numpy(), pts.iloc[:, 1].to_numpy()
    h = size / 2
    return gpd.GeoDataFrame({"cell": [csquare(x, y, size) for x, y in zip(xc, yc)]},
                            geometry=shapely.box(xc - h, yc - h, xc + h, yc + h), crs=CRS)


def step_select(a) -> None:
    sel_dir = a.out / "selected"
    sel_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(list(a.inputs.glob("*.fgb")) + list(a.inputs.glob("*.shp")))
    rows = []
    for f in files:
        group = f.stem.split("__")[0]
        if group not in GROUPS:
            continue
        n_feat = pyogrio.read_info(f)["features"]
        for k, start in enumerate(range(0, max(n_feat, 1), CHUNK)):
            name = f.stem if n_feat <= CHUNK else f"{f.stem}__part{k}"
            if (sel_dir / f"{name}.fgb").exists():   # resumable
                continue
            d = pyogrio.read_dataframe(f, skip_features=start, max_features=CHUNK)
            row = select_part(d, f, group, name, sel_dir)
            if row:
                rows.append(row)
    by_map = a.out / "selected_by_map.csv"
    pd.DataFrame(rows).to_csv(by_map, mode="a", header=not by_map.exists(), index=False)


def select_part(d, f, group, name, sel_dir):
        d.columns = [c.upper() if c != "geometry" else c for c in d.columns]
        for c in ["GUI", "POLYGON", "ORIG_HAB", "ORIG_CLASS", "DET_NAME", "DET_DATE", "SUM_CONF"]:
            if c not in d:
                d[c] = None
        gui = str(d.GUI.dropna().iloc[0]) if d.GUI.notna().any() else f.stem.split("__")[1].split("_")[0]
        if group == "IND":
            if gui not in INDIVIDUAL:
                log(f"skip {f.name}: not in the Caribbean selection rules")
                return None
            prio, sub, yr0 = INDIVIDUAL[gui]
        else:
            prio, sub, yr0 = GROUP_PRIORITY[group], 0, 0
        d = d[d.geometry.notna()]
        if d.crs is None:
            d = d.set_crs(CRS)
        d = d.to_crs(CRS)
        d["geometry"] = polygons_only(shapely.set_precision(make_valid(shapely.force_2d(d.geometry.values)),
                                                            PRECISION))
        d = d.explode(index_parts=False)
        d = d[d.geometry.geom_type.eq("Polygon") & (d.area >= MIN_AREA)]
        years = [year(v) or yr0 for v in d.DET_DATE.astype(str)]
        hab = d.ORIG_HAB.fillna("").astype(str)
        out = gpd.GeoDataFrame({
            "Map_id": d.GUI.fillna(gui).astype(str), "Polygon": d.POLYGON.astype(str), "Hab_origin": hab,
            "Orig_class": d.ORIG_CLASS.fillna("").astype(str), "Eunis_code": "", "Hab_class": "", "Eunis_ver": "",
            "Eunis_name": "", "Anxi_code": "", "Anxi_name": "", "Ai_subtype": "", "Ospar_hab": "",
            "Library": GROUPS[group], "determiner": d.DET_NAME.fillna("").astype(str),
            "Det_date": d.DET_DATE.astype(str).replace({"NaT": "", "None": ""}),
            "Source": GROUPS[group] + " (" + d.GUI.fillna(gui).astype(str) + ")", "Item": ITEM,
            "Match_rule": "Caribbean seagrass input", "Comp": "", "Comp_type": "",
            "Sum_conf": pd.to_numeric(d.SUM_CONF, errors="coerce").fillna(-1).astype(int),
            "Priority": prio, "Year": years, "Subprio": sub,
        }, geometry=d.geometry.values, crs=CRS)
        pyogrio.write_dataframe(out, sel_dir / f"{name}.fgb", driver="FlatGeobuf")
        area = out.to_crs(AREA_CRS).area.sum() / 1e6
        log(f"select {name}: {len(out)} polygons, {area:.1f} km2 (priority {prio}.{sub})")
        return {"file": name, "Map_id": gui, "group": group, "Priority": prio, "Subprio": sub,
                "n": len(out), "area_km2": round(area, 3)}


SORT_KEYS = ["Priority", "Subprio", "Year", "Sum_conf", "Map_id", "Polygon"]
SORT_ASC = [True, True, False, False, True, True]
BLOCK = 1.0   # memory: the region is processed in 1 degree blocks (C-squares 1 degree cells)


def read_selected(a, bounds):
    """Selected polygons whose bounding box meets ``bounds`` (FlatGeobuf spatial index), by rank."""
    parts = [pyogrio.read_dataframe(f, bbox=bounds) for f in sorted((a.out / "selected").glob("*.fgb"))]
    parts = [p_ for p_ in parts if len(p_)]
    if not parts:
        return None
    sel = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), geometry="geometry", crs=CRS)
    return sel.sort_values(SORT_KEYS, ascending=SORT_ASC).reset_index(drop=True)


def step_resolve(a) -> None:
    """Noded overlay tile by tile (0.1 degree C-squares; dense tiles by 0.01 degree cells), reading
    the selected polygons block by block (1 degree) so that memory stays bounded. The rank is the
    same in every block (sort on attributes only), so the result does not depend on the blocks."""
    files = sorted((a.out / "selected").glob("*.fgb"))
    b = np.array([pyogrio.read_info(f)["total_bounds"] for f in files])
    bounds = (b[:, 0].min(), b[:, 1].min(), b[:, 2].max(), b[:, 3].max())
    blocks = tiles_for(bounds, BLOCK)
    log(f"resolve: {len(files)} selected files, {len(blocks)} C-squares 1 degree blocks; rank: priority, "
        "sub-priority (resolution), year, SUM_CONF")
    out = a.out / "composite.gpkg"
    if out.exists():
        out.unlink()
    n_out, t0 = 0, time.time()
    for bk, (bcode, bgeom) in enumerate(zip(blocks.cell, blocks.geometry.values), 1):
        sel = read_selected(a, bgeom.bounds)
        if sel is None:
            continue
        tree = STRtree(sel.geometry.values)
        tiles = tiles_for(bgeom.bounds, TILE)
        tiles = tiles[shapely.within(shapely.centroid(tiles.geometry.values), bgeom)]
        geoms = sel.geometry.values
        for cell, tile in zip(tiles.cell, tiles.geometry.values):
            idx = np.sort(tree.query(tile, predicate="intersects"))
            if not len(idx):
                continue
            cells = [(tile, idx)]
            if len(idx) > MAX_PER_TILE:
                sub = tiles_for(tile.bounds, CELL)
                sub = sub[shapely.within(shapely.centroid(sub.geometry.values), tile)]
                cells = [(c, np.sort(tree.query(c, predicate="intersects"))) for c in sub.geometry.values]
            kept_geom, kept_idx = [], []
            for cgeom, cidx in cells:
                if len(cidx):
                    g_, i_ = resolve_cell(geoms, cidx, cgeom, precision=PRECISION, min_area=MIN_AREA)
                    kept_geom += g_
                    kept_idx += i_
            if not kept_idx:
                continue
            part = sel.iloc[kept_idx].drop(columns="geometry").copy()
            part["Csquare01"] = cell
            part["Block"] = bcode
            g = gpd.GeoDataFrame(part, geometry=kept_geom, crs=CRS).explode(index_parts=False)
            g = g[(g.geometry.geom_type == "Polygon") & (g.area >= MIN_AREA)]
            pyogrio.write_dataframe(g, out, layer="polygons", append=out.exists())
            n_out += len(g)
        log(f"resolve block {bk}/{len(blocks)} {bcode}: {len(sel)} input polygons, {n_out} pieces so far, "
            f"{time.time() - t0:.0f} s")
    log(f"resolve done: {n_out} polygons -> {out}")


def _dissolve(comp, keys):
    rows, geoms = [], []
    for vals, g in comp.groupby(keys, sort=False):
        gv = g.geometry.values
        if len(gv) == 1:
            u = gv[0]
        else:
            p_ = shapely.point_on_surface(gv)
            key = np.floor(shapely.get_x(p_) / CELL).astype(np.int64) * 100_000 + \
                np.floor(shapely.get_y(p_) / CELL).astype(np.int64)
            per_cell = []
            for k in np.unique(key):
                cg = gv[key == k]
                try:
                    per_cell.append(cg[0] if len(cg) == 1 else shapely.coverage_union_all(cg))
                except shapely.errors.GEOSException:
                    per_cell.append(shapely.union_all(cg))
            pc = np.array(per_cell, dtype=object)
            try:   # the cells come from one noded overlay on the 0.00001 degree grid: a coverage
                u = pc[0] if len(pc) == 1 else shapely.coverage_union_all(pc)
                if not u.is_valid:
                    raise shapely.errors.GEOSException("invalid coverage union")
            except shapely.errors.GEOSException:
                u = shapely.union_all(pc, grid_size=PRECISION)
        parts = [p for p in shapely.get_parts(polygons_only([u])[0]) if p.area >= MIN_AREA]
        n_in = np.ones(len(parts), int)
        if "N_pieces" not in g:
            hit = STRtree(shapely.point_on_surface(gv)).query(np.array(parts, dtype=object), predicate="contains")
            n_in = np.bincount(hit[0], minlength=len(parts)) if len(parts) else []
        for part, k in zip(parts, n_in):
            rows.append(dict(zip(keys, vals)) | {"N_pieces": int(k)})
            geoms.append(part)
    return gpd.GeoDataFrame(rows, geometry=geoms, crs=CRS)


def step_dissolve(a) -> None:
    """Merge the pieces with the same information: first inside each 1 degree block (written to
    disk block by block, layer ``blocks_dissolved``; resumable), then the polygons that touch a
    block edge are merged across the blocks (second pass)."""
    src = a.out / "composite.gpkg"
    tmp = a.out / "dissolve_blocks.gpkg"
    blocks = pyogrio.read_dataframe(src, layer="polygons", columns=["Block"], read_geometry=False).Block.unique()
    done = set(pyogrio.read_dataframe(tmp, layer="interior", columns=["Block"], read_geometry=False).Block) \
        if tmp.exists() and "interior" in pyogrio.list_layers(tmp)[:, 0] else set()
    t0 = time.time()
    for n, bcode in enumerate(blocks, 1):
        if bcode in done:
            continue
        comp = pyogrio.read_dataframe(src, layer="polygons", where=f"Block = '{bcode}'")
        keys = [k for k in DISSOLVE_KEYS if k in comp.columns]
        comp[keys] = comp[keys].fillna("")
        d = _dissolve(comp, keys)
        d["Block"] = bcode
        b = np.round(shapely.bounds(d.geometry.values) / BLOCK, 6)
        edge = (b == np.round(b)).any(axis=1)   # touches a 1 degree line
        for layer, part in (("edge", d[edge]), ("interior", d[~edge])):
            if len(part) or layer == "interior":
                pyogrio.write_dataframe(part, tmp, layer=layer, append=tmp.exists() and layer in
                                        pyogrio.list_layers(tmp)[:, 0])
        log(f"dissolve block {n}/{len(blocks)} {bcode}: {len(comp)} -> {len(d)} polygons, {time.time() - t0:.0f} s")
    edge = pyogrio.read_dataframe(tmp, layer="edge").drop(columns="Block")
    keys = [k for k in DISSOLVE_KEYS if k in edge.columns]
    edge[keys] = edge[keys].fillna("")
    pieces = edge.groupby(keys).N_pieces.sum()
    merged = _dissolve(edge.drop(columns="N_pieces"), keys).drop(columns="N_pieces")
    merged = merged.merge(pieces.reset_index(), on=keys, how="left")   # summed over the group
    inner = pyogrio.read_dataframe(tmp, layer="interior").drop(columns="Block")
    out = gpd.GeoDataFrame(pd.concat([inner, merged], ignore_index=True), geometry="geometry", crs=CRS)
    out.insert(0, "objectid", np.arange(1, len(out) + 1))
    pyogrio.write_dataframe(out, src, layer="polygons_dissolved")
    log(f"dissolve done: {len(out)} polygons ({len(edge)} on block edges merged into {len(merged)}), "
        f"{out.to_crs(AREA_CRS).area.sum() / 1e6:.1f} km2")


def step_check(a) -> None:
    d = pyogrio.read_dataframe(a.out / "composite.gpkg", layer="polygons_dissolved")
    g = d.geometry.values
    left, right = STRtree(g).query(g, predicate="overlaps")
    m = left < right
    area = gpd.GeoSeries(shapely.intersection(g[left[m]], g[right[m]]), crs=CRS).to_crs(AREA_CRS).area
    log(f"check: {int(m.sum())} overlapping pairs, {area.sum():.1f} m2 (> 1 m2: {int((area > 1).sum())}); "
        f"invalid: {int((~d.is_valid).sum())}")


def step_export(a) -> None:
    d = pyogrio.read_dataframe(a.out / "composite.gpkg", layer="polygons_dissolved")
    d["geometry"] = polygons_only(make_valid(d.geometry.values))
    d = d[~d.geometry.is_empty]
    d["Area_km2"] = (d.to_crs(AREA_CRS).area / 1e6).round(6)
    out = a.out / "composite_caribbean_wgs84.gpkg"
    if out.exists():
        out.unlink()
    pyogrio.write_dataframe(d, out, layer="polygons")
    log(f"export: {len(d)} polygons, {d.Area_km2.sum():.1f} km2 -> {out} (invalid: {(~d.is_valid).sum()})")


def step_compare(a) -> None:
    new = pyogrio.read_dataframe(a.out / "composite_caribbean_wgs84.gpkg", layer="polygons",
                                 columns=["Map_id", "Area_km2"], read_geometry=False)
    new_area = new.groupby("Map_id").Area_km2.sum()
    old = pyogrio.read_dataframe(a.old, columns=["map_id"])
    old = old[old.geometry.notna()]
    if old.crs is None:
        old = old.set_crs(CRS)
    old = old.to_crs(CRS)
    c = shapely.point_on_surface(old.geometry.values)
    old = old[(shapely.get_x(c) < -50) & (shapely.get_y(c) < 35)]
    old_area = old.to_crs(AREA_CRS).assign(a=lambda x: x.area / 1e6).groupby("map_id").a.sum()
    cmp = pd.DataFrame({"area_km2_2026": new_area, "area_km2_2025": old_area}).fillna(0).round(3)
    cmp["diff_km2"] = (cmp.area_km2_2026 - cmp.area_km2_2025).round(3)
    cmp.index.name = "Map_id"
    cmp.sort_values("area_km2_2026", ascending=False).to_csv(a.out / "compare_2025_caribbean.csv")
    log(f"compare: 2026 {new_area.sum():.1f} km2 in {len(new_area)} maps; 2025 {old_area.sum():.1f} km2 in "
        f"{len(old_area)} maps")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--old", type=Path, help="2025 composite polygons, for the comparison")
    p.add_argument("--steps", nargs="+", default=["select", "resolve", "dissolve", "check", "export", "compare"])
    a = p.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    for s in ["select", "resolve", "dissolve", "check", "export"]:
        if s in a.steps:
            globals()[f"step_{s}"](a)
    if "compare" in a.steps and a.old:
        step_compare(a)


if __name__ == "__main__":
    sys.exit(main())
