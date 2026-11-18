#!/usr/bin/env python
import glob
import os
import sys

import geopandas as gpd
import h5py
import matplotlib
import openslide
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

name, slide = sys.argv[1:3]


def tissue(run):
    return gpd.read_file(f"{run}/contours_geojson/{name}.geojson").geometry.union_all()


def tiles(run, folder):
    path = f"{run}/{folder}/patches/{name}_patches.h5"
    if not os.path.exists(path):
        return set()
    with h5py.File(path) as f:
        return set(map(tuple, f["coords"][:]))


stored, icc = tissue("stored"), tissue("icc")
lost, gained = stored.difference(icc), icc.difference(stored)


def pct(area):
    return 100 * area / stored.area if stored.area else float("nan")


row = {
    "name": name,
    "tissue_stored": stored.area,
    "tissue_icc": icc.area,
    "tissue_change_pct": pct(icc.area - stored.area),
    "tissue_lost_pct": pct(lost.area),
    "tissue_gained_pct": pct(gained.area),
}
for folder in sorted(os.path.basename(p) for p in glob.glob("stored/tiles_*")):
    before, after = tiles("stored", folder), tiles("icc", folder)
    row[f"{folder}_stored"] = len(before)
    row[f"{folder}_icc"] = len(after)
    row[f"{folder}_lost"] = len(before - after)
    row[f"{folder}_gained"] = len(after - before)
pd.DataFrame([row]).to_csv(f"{name}.tsv", sep="\t", index=False)

wsi = openslide.OpenSlide(slide)
width, height = wsi.dimensions
fig, ax = plt.subplots(figsize=(6, 6 * height / width))
ax.imshow(wsi.get_thumbnail((1000, 1000)), extent=(0, width, height, 0))
for shape, colour in ((lost, "#eb6834"), (gained, "#2a78d6")):
    if not shape.is_empty:
        gpd.GeoSeries([shape]).plot(ax=ax, color=colour, alpha=0.8)
ax.set_title(f"orange: tissue only as stored ({row['tissue_lost_pct']:.1f}%)\n"
             f"blue: tissue only with ICC ({row['tissue_gained_pct']:.1f}%)", fontsize=8, loc="left")
ax.axis("off")
fig.savefig(f"{name}_mask.png", dpi=150, bbox_inches="tight")
