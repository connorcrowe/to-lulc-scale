## SLICER.PY
# This script makes requests of the WMS from the City of Toronto Map Server to create and save smaller tiles of the 2024 aerial map.

# Imports
from owslib.wms import WebMapService
import requests
from PIL import Image
from io import BytesIO
import rasterio
import rasterio.plot
import numpy as np
from pyproj import Transformer
from tqdm import tqdm
from itertools import product

# WMS - Aerial Map of the City of Toronto
wms_url = "https://gis.toronto.ca/arcgis/services/basemap/cot_ortho/MapServer/WMSServer"

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
    # Requests a aerial tile with specific bounding box and resolution from the WMS of the larger City of Toronto aerial map

    # @bounding_box - Bounding box of lat lon coords to define the tile (upper left lon, lower right lat, lower right lon, upper right lat)
    # @resolution   - Ouput resolution of each tile, resolution x resolution, in pixels

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

    with rasterio.open(BytesIO(response.content)) as src:
        image = src.read()
        meta = src.meta.copy()
    
    return image, meta

# MAIN LOOP
stop_after = 10
tiles = list(product(x_coords, y_coords))

for x, y in tqdm(tiles, desc="Downloading tiles"):
    if stop_after <= 0: break
    stop_after -= 1

    # Get lat/lon coords of upper left and bottom right corners
    ul_lon, ul_lat = to_latlon.transform(x, y + step)
    lr_lon, lr_lat = to_latlon.transform(x + step, y)    

    # Request image tile from WMS
    image, meta = request_slice([ul_lon, lr_lat, lr_lon, ul_lat])
    
    # Skip image if mostly white pixels (borders)
    if np.mean(np.array(image)) > 250: 
        continue

    # Show image 
    rasterio.plot.show(image)
    
    # TODO - Save image, check if image with same coords saved already and skip