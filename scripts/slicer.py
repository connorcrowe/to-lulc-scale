## SLICER.PY
# This script makes requests of the WMS from the City of Toronto Map Server to create and save smaller tiles of the 2024 aerial map.

# Imports
import os
import requests
from owslib.wms import WebMapService

from PIL import Image
from io import BytesIO

import numpy as np

os.environ["PROJ_DATA"] = os.path.join(os.environ["VIRTUAL_ENV"], "Lib", "site-packages", "rasterio", "proj_data")
import rasterio
import rasterio.plot
from rasterio.transform import from_bounds

from pyproj import Transformer
from tqdm import tqdm
from itertools import product

# WMS - Aerial Map of the City of Toronto
wms_url = "https://gis.toronto.ca/arcgis/services/basemap/cot_ortho/MapServer/WMSServer"

# Directory to save files to
output_dir = "data/tiles/"

# TRANSFORMERS - Used to turn lat/lon coords to UTM (for adding steps in meters) and back
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32617", always_xy=True)
to_latlon = Transformer.from_crs("EPSG:32617", "EPSG:4326", always_xy=True)

# EXTENT - Lat/Lon extent of the WMS aerial image
#min_lon, max_lon = -79.6799539999999951, -79.0702129999999954
#min_lat, max_lat = 43.5483800000000016, 43.9100490000000008 
min_lon, max_lon = -79.6516774965740666, -79.1001631049245191
min_lat, max_lat = 43.5712933809708431, 43.8656125139796274

# UTM EXTENT - Set WMS aerial bounding box coords to UTM 
min_x, min_y = to_utm.transform(min_lon, min_lat)
max_x, max_y = to_utm.transform(max_lon, max_lat)

# TILE COORDS - Create list of coords of tiles to request
step = 256
x_coords = np.arange(min_x, max_x, step)
y_coords = np.arange(min_y, max_y, step)

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
        'srs': 'EPSG:4326',
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
stop_after = 10
skipped = 0
broken = 0
saved = 0
existing = 0
tiles = list(product(x_coords, y_coords))

for x, y in tqdm(tiles, desc="Downloading tiles"):
    if stop_after <= 0: break
    

    # Set filepath based on tile origin
    filename = f"tile_{int(x)}_{int(y)}.tif"
    filepath = os.path.join(output_dir, filename)

    # Skip if tile already saved to dir
    if os.path.exists(filepath): 
        existing += 1
        continue

    # Get lat/lon coords of upper left and bottom right corners
    ul_lon, ul_lat = to_latlon.transform(x, y + step)
    lr_lon, lr_lat = to_latlon.transform(x + step, y)    

    # Request image tile from WMS
    try:
        image, meta = request_slice([ul_lon, lr_lat, lr_lon, ul_lat])
    except Exception as e:
        broken += 1
        #print(f"\nSkipping tile at ({x}, {y}) due to error: {e}")
        continue

    # Skip image if mostly white pixels (borders)
    if np.mean(np.array(image)) > 250: 
        skipped += 1
        continue

    # Create affine transform from bounding box
    transform = from_bounds(ul_lon, lr_lat, lr_lon, ul_lat, 512, 512)

    # Save tile as GeoTIFF
    with rasterio.open(
        filepath, "w",
        driver="GTiff",
        height=512, width=512,
        count=3,
        dtype='uint8',
        crs="EPSG:4326",
        transform=transform
    ) as dst:
        dst.write(image)
    saved += 1
    stop_after -= 1

print(f'Existing:      {existing}')
print(f'Tiles Broken:  {broken}')
print(f'Tiles Skipped: {skipped}')
print(f'Tiles Saved:   {saved}')
