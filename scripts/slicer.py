"""
Slicer.py: Requests configurable size and resolution tiles from the City of Toronto Map Server WMS to collect and save tiles of the 2024 aerial map of Toronto.

    Done to generate a directory of smaller size tiles for easier ML classification in the scripts/predictor.py script. 
    Aerial image map collected in ESPG:3857
    Aerial image credit to City of Toronto Open Data Map Server    

    @tile_size_m - Adjusts tile size in meters
    @tile_resolution - Adjusts tile resolution in pixels

"""
# Imports
import os
import requests
os.environ["PROJ_DATA"] = os.path.join(os.environ["VIRTUAL_ENV"], "Lib", "site-packages", "rasterio", "proj_data")

import numpy as np
import rasterio
import rasterio.plot
import time

from rasterio.transform import from_bounds
from owslib.wms import WebMapService
from PIL import Image
from io import BytesIO
from tqdm import tqdm
from itertools import product
from pyproj import Transformer


import matplotlib.pyplot as plt
from rasterio.plot import reshape_as_image

# WMS - Aerial Map of the City of Toronto
WMS_URL = "https://gis.toronto.ca/arcgis/rest/services/basemap/cot_ortho_2023_color_10cm/MapServer/export"

# Directory to save files to
DIR_OUT_TILES = "data/tiles/"

# Parameters for retrying failed requests
MAX_RETRIES = 5
RETRY_DELAY = 1 # (seconds)

# Set tile dimensions and resolution
tile_resolution = 704
tile_size_m = 352

# Calculate meters/pixel based on target tile size and resolution
meters_per_pixel = tile_size_m / tile_resolution  # Should be 0.5 m/px

# Convert meters to EPSG:3857 units per pixel at TARGET_LAT
pixel_spacing_x = meters_per_pixel 
pixel_spacing_y = meters_per_pixel  

# Calculate step size in projected units for a 1024x1024m tile
tile_size_x_units = pixel_spacing_x * tile_resolution
tile_size_y_units = pixel_spacing_y * tile_resolution

def meters_to_webmercator_bounds(x_center, y_center, width_units, height_units):
    """
    Given a center point in EPSG:3857 and tile size in Web Mercator units,
    returns a bounding box [xmin, ymin, xmax, ymax].
    """
    half_w = width_units / 2.0
    half_h = height_units / 2.0
    return [x_center - half_w, y_center - half_h, x_center + half_w, y_center + half_h]

def old_request_slice(bounding_box, resolution):
    """
    Requests a aerial tile with specific bounding box and resolution from the WMS of the larger City of Toronto aerial map.

    @bounding_box - Bounding box of lat lon coords to define the tile (upper left lon, lower right lat, lower right lon, upper right lat)
    @resolution   - Ouput resolution of each tile, resolution x resolution, in pixels
    """

    # Request tile from WMS
    response = requests.get(WMS_URL, params={
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

def request_slice(bounding_box, resolution, out_path):
    """
    Requests a aerial tile with specific bounding box and resolution from the ARCGIS api of the larger City of Toronto aerial map and saves it to a file.

    @bounding_box - Bounding box of lat lon coords to define the tile (upper left lon, lower right lat, lower right lon, upper right lat)
    @resolution   - Ouput resolution of each tile, resolution x resolution, in pixels
    """
    params = {
        "f": "image",
        "bbox": ",".join(map(str, bounding_box)),
        "bboxSR": "3857",
        "imageSR": "3857",
        "size": f"{resolution},{resolution}",
        "format": "tiff",
        "transparent": "false"
    }
    
    response = requests.get(WMS_URL, params=params)

    image = Image.open(BytesIO(response.content))
    
    image_np = np.array(image)

    if np.mean(image_np) > 253: return 
    transform = from_bounds(*bounding_box, width=resolution, height=resolution)

    # Save as GeoTIFF
    with rasterio.open(
        out_path,
        "w",
        driver="GTiff",
        height=resolution,
        width=resolution,
        count=3,
        dtype=image_np.dtype,
        crs="EPSG:3857",
        transform=transform
    ) as dst:
        for i in range(3):
            dst.write(image_np[:, :, i], i + 1) 

def main():
    # ESPG:3857 extent (in meters)
    min_x, min_y = -8866839.3637663740664721, 5399347.6239214604720473 
    max_x, max_y = -8805463.7355606518685818, 5444639.5874546216800809

    x_steps = np.arange(min_x, max_x, tile_size_m)
    y_steps = np.arange(min_y, max_y, tile_size_m)

    tiles = list(product(x_steps, y_steps))

    saved, broken = 0, 0

    for x, y in tqdm(tiles, desc="Downloading tiles"):
    
        filename = f"tile_{int(x)}_{int(y)}.tif"
        filepath = os.path.join(DIR_OUT_TILES, filename)

        # Check if the tile already exists
        if os.path.exists(filepath): continue

        center_x = x + tile_size_x_units / 2
        center_y = y + tile_size_y_units / 2
        bbox = meters_to_webmercator_bounds(center_x, center_y, tile_size_x_units, tile_size_y_units)

        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                request_slice(bbox, tile_resolution, filepath)
                success = True
                break  # Exit retry loop on success
            except Exception as e:
                print(f"\nAttempt {attempt} failed for tile {filename}: {e}")
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAY * 1000
                    time.sleep(delay)
                else:
                    broken += 1

        if success:
            saved += 1

    print(f'Tiles Saved:   {saved}')
    print(f'Tiles Broke:   {broken}')

if __name__ == "__main__": main()