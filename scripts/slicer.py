## SLICER.PY
# This script makes requests of the WMS from the City of Toronto Map Server to create and save smaller tiles of the 2024 aerial map.

# Imports
import os
os.environ["PROJ_DATA"] = os.path.join(os.environ["VIRTUAL_ENV"], "Lib", "site-packages", "rasterio", "proj_data")

import requests
from owslib.wms import WebMapService

from PIL import Image
from io import BytesIO

import numpy as np


import rasterio
import rasterio.plot
from rasterio.transform import from_bounds

from tqdm import tqdm
from itertools import product

# WMS - Aerial Map of the City of Toronto
wms_url = "https://gis.toronto.ca/arcgis/services/basemap/cot_ortho/MapServer/WMSServer"

# Directory to save files to
output_dir = "data/tiles/"

# Set tile dimensions and resolution
tile_size_m = 512
tile_resolution = 512
meters_per_pixel = tile_size_m / tile_resolution

# EXTENT 
# - Lat/Lon extent of the WMS aerial image
#min_lon, max_lon = -79.6516774965740666, -79.1001631049245191
#min_lat, max_lat = 43.5712933809708431, 43.8656125139796274
# - ESPG:3857 Extent (m)
min_x, min_y = -8866839.3637663740664721,5399347.6239214604720473 
max_x, max_y = -8805463.7355606518685818,5444639.5874546216800809

x_steps = np.arange(min_x, max_x, tile_size_m)
y_steps = np.arange(min_y, max_y, tile_size_m)

tiles = list(product(x_steps, y_steps))

def request_slice(bounding_box, resolution=512):
    """
    Requests a aerial tile with specific bounding box and resolution from the WMS of the larger City of Toronto aerial map.

    @bounding_box - Bounding box of lat lon coords to define the tile (upper left lon, lower right lat, lower right lon, upper right lat)
    @resolution   - Ouput resolution of each tile, resolution x resolution, in pixels
    """

    # Request tile from WMS
    response = requests.get(wms_url, params={
        'service': 'WMS',
        'version': '1.1.1',
        'request': 'GetMap',
        'layers': '0',
        'styles': '',
        'bbox': ','.join(map(str, bounding_box)),
        'width': resolution,
        'height': resolution,
        'srs': 'EPSG:3857',
        'format': 'image/tiff'
    })

    if not response.ok:
        raise Exception(f"WMS request failed with status code {response.status_code}")
    
    content_type = response.headers.get("Content-Type", "").lower()
    if "tiff" not in content_type:
        raise ValueError(f"Unexpected content type: {content_type}\nLikely an error tile or service issue.")

    try:
        with rasterio.open(BytesIO(response.content)) as src:
            image = src.read()
            meta = src.meta.copy()
    except rasterio.errors.RasterIOError as e:
        raise ValueError(f"Failed to read GeoTIFF from response. Possibly invalid TIFF. Deatils:\n{e}")
    
    return image, meta

# MAIN LOOP
stop_after = 5000
skipped, broken, saved = 0, 0, 0

for x, y in tqdm(tiles, desc="Downloading tiles"):
    if saved >= stop_after: break
    
    # Set filepath based on tile origin
    filename = f"tile_{int(x)}_{int(y)}.tif"
    filepath = os.path.join(output_dir, filename)
    if os.path.exists(filepath): continue

    bbox = [x, y, x + tile_size_m, y + tile_size_m]

    # Request image tile from WMS
    try:
        image, meta = request_slice(bbox, tile_resolution)

        # Skip image if mostly white pixels (borders)
        if np.mean(np.array(image)) > 250: continue

        # Save tile as GeoTIFF
        with rasterio.open(
            filepath, "w",
            driver="GTiff",
            height=tile_resolution, 
            width=tile_resolution,
            count=3,
            dtype='uint8',
            crs="EPSG:3857",
            transform=from_bounds(*bbox, tile_resolution, tile_resolution)
        ) as dst:
            dst.write(image)
    
    except Exception as e:
        broken += 1
        print(f"\nFailed to write tile {filename}: {e}")

    saved += 1

print(f'Tiles Broken:  {broken}')
print(f'Tiles Saved:   {saved}')