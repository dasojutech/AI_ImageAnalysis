import os
import numpy as np
import rasterio
import geopandas as gpd
from rasterio.mask import mask
from rasterio.windows import Window

# -----------------------------
# Paths
# -----------------------------
raster_path = r"C:\projects\image_analysis\AI_ImageAnalysis\data\RGB\S2A_MSIL2A_20241219T185811_R113_T10SEG_20241219T221845_RGB.tif"
aoi_path =r"C:\projects\image_analysis\AI_ImageAnalysis\data\vectors\sf_buildings.geojson"

output_clipped = r"C:\projects\image_analysis\AI_ImageAnalysis\output\clipped.tif"
tile_folder = r"C:\projects\image_analysis\AI_ImageAnalysis\output\tiles"

os.makedirs("data/processed", exist_ok=True)
os.makedirs(tile_folder, exist_ok=True)

# -----------------------------
# Load AOI
# -----------------------------
aoi = gpd.read_file(aoi_path)

# -----------------------------
# Clip raster to AOI
# -----------------------------
with rasterio.open(raster_path) as src:

    aoi = aoi.to_crs(src.crs)

    clipped_img, clipped_transform = mask(src, aoi.geometry, crop=True)

    meta = src.meta.copy()

meta.update({
    "height": clipped_img.shape[1],
    "width": clipped_img.shape[2],
    "transform": clipped_transform
})

# -----------------------------
# Normalize bands
# -----------------------------
clipped_img = clipped_img.astype("float32")
clipped_img = clipped_img / clipped_img.max()

meta.update(dtype="float32")

with rasterio.open(output_clipped, "w", **meta) as dst:
    dst.write(clipped_img)

print("Clipped + normalized image saved")

# -----------------------------
# Tile imagery for ML
# -----------------------------
tile_size = 256

with rasterio.open(output_clipped) as src:

    tile_id = 0

    for x in range(0, src.width, tile_size):
        for y in range(0, src.height, tile_size):

            window = Window(x, y, tile_size, tile_size)

            tile = src.read(window=window)

            if tile.shape[1] != tile_size or tile.shape[2] != tile_size:
                continue

            transform = src.window_transform(window)

            tile_meta = src.meta.copy()

            tile_meta.update({
                "height": tile_size,
                "width": tile_size,
                "transform": transform
            })

            tile_path = f"{tile_folder}/tile_{tile_id}.tif"

            with rasterio.open(tile_path, "w", **tile_meta) as dst:
                dst.write(tile)

            tile_id += 1

print("Total tiles created:", tile_id)