import os
import rasterio
import geopandas as gpd
from rasterio.features import rasterize

# -----------------------------
# Paths
# -----------------------------
tile_folder = r"C:\projects\image_analysis\AI_ImageAnalysis\output\tiles"              # Input image tiles
building_shp = r"C:\projects\image_analysis\AI_ImageAnalysis\data\vectors\sf_buildings.geojson"
mask_folder = r"C:\projects\image_analysis\AI_ImageAnalysis\output\masks"

os.makedirs(mask_folder, exist_ok=True)

# -----------------------------
# Load building footprints
# -----------------------------
buildings = gpd.read_file(building_shp)

# -----------------------------
# Loop through each tile
# -----------------------------
for tile_file in os.listdir(tile_folder):
    if not tile_file.endswith(".tif"):
        continue

    tile_path = os.path.join(tile_folder, tile_file)

    with rasterio.open(tile_path) as src:
        buildings_crs = buildings.to_crs(src.crs)

        # Clip using bounding box
        minx, miny, maxx, maxy = src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top
        buildings_tile = buildings_crs.cx[minx:maxx, miny:maxy]

        # Rasterize
        mask_data = rasterize(
            [(geom, 1) for geom in buildings_tile.geometry],
            out_shape=(src.height, src.width),
            transform=src.transform,
            fill=0,
            dtype='uint8'
        )

        # Save mask
        mask_path = os.path.join(mask_folder, tile_file.replace(".tif","_mask.tif"))
        meta = src.meta.copy()
        meta.update(count=1, dtype='uint8')

        with rasterio.open(mask_path, "w", **meta) as dst:
            dst.write(mask_data, 1)