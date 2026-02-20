# src/ingestion/sentinel.py
from pystac_client import Client
import os
import requests

def download_sentinel(config, asset_key="B04", out_dir="../outputs/raster"):
    os.makedirs(out_dir, exist_ok=True)

    client = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

    # ✅ Correct
    items = client.search(
        collections=["sentinel-s2-l2a-cogs"],  # note the plural and list
        bbox=config["aoi"]["bbox"],
        datetime=f"{config['sentinel']['start_date']}/{config['sentinel']['end_date']}"
    ).get_items()

    first_item = next(items)

    asset_url = first_item.assets[asset_key].href
    filename = os.path.join(out_dir, f"{first_item.id}_{asset_key}.tif")

    if not os.path.exists(filename):
        r = requests.get(asset_url, stream=True)
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return filename