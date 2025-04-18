"""
Predictor.py: Runs LULC classification on aerial image tiles from the City of Toronto.

    Tiles collected from City of Toronto Open Data Web Map Server - saved by scripts/slicer.py
    Model built and trained by me in connorcrowe/to-lulc-aiml
"""

# Imports
import os
import rasterio

import numpy as np
import matplotlib.pyplot as plt
import tensorflow.keras.backend as K

from tensorflow.keras.models import load_model
from rasterio.plot import reshape_as_image
from rasterio.crs import CRS
from patchify import patchify
from patchify import unpatchify

from pyproj import datadir

# Use pyproj's known-good proj.db location
os.environ["PROJ_DATA"] = str(datadir.get_data_dir())

# Set directories
DIR_IN_TILES = 'data/tiles/'
DIR_OUT_PREDICTIONS = 'data/predictions/'

# Set classification model
PATH_MODEL = 'model/unet_v2_1.keras'

# Function - Import tile
def import_tiles():
    """
    Lazily loads tiles from directory using a generator to prevent running out of memory loading all at once.
    """
    for filename in os.listdir(DIR_IN_TILES):
        if filename.endswith('.tif'):
            filepath = os.path.join(DIR_IN_TILES, filename)

            with rasterio.open(filepath) as src:
                image = src.read()
                yield (image, src.meta.copy(), filename)

# Function - Predict tile
def predict_tile(model, tile):
    """
    Runs LULC model on a single tile
    """
    # Reshape from (bands, size, size) to (size, size, bands)  
    tile_normalized = tile.astype(np.float32) / 255.0
    tile_reshaped = reshape_as_image(tile_normalized)                                              #  (2048, 2048, 3)
    tile_size = tile_reshaped.shape[0]

    # Split into patches of model input size to predict (128 x 128)
    patch_size = 128
    patch_step = 64
    patches = patchify(tile_reshaped, (patch_size, patch_size, 3), step = patch_step)   # (16, 16, 128, 128, 3)

    # Flatten to one list of patch_size x patch_size patches
    patches_reshaped = patches.reshape(-1, patch_size, patch_size, 3)                   # (256, 128, 128, 3)
    
    # Predict patches
    prediction = model.predict(patches_reshaped)                                        # (256, 128, 128, 5)

    # Unpatchify back to original shape
    prediction_reshaped = prediction.reshape(
        patches.shape[0], patches.shape[0], patch_size, patch_size, 5)               # (4, 4, 1, 128, 128, 5)
    
    # Collapse to highest likelihood class for each pixel
    prediction_classes = np.argmax(prediction_reshaped, axis=-1)                       # (2048, 2048)

    # REASSEMBLE IMAGE
    # Make output of proper shape with zeros, and a weight matrix to track tile contributions to each pixel
    blended_prediction = np.zeros((patches.shape[0] * patch_step + patch_size,
                                   patches.shape[0] * patch_step + patch_size), dtype=np.float32)
    weight_matrix = np.zeros_like(blended_prediction, dtype=np.float32)

    # Blend patches together
    for i in range(patches.shape[0]):
        for j in range(patches.shape[0]):
            x_start = i * patch_step
            x_end = x_start + patch_size
            y_start = j * patch_step
            y_end = y_start + patch_size

            blended_prediction[x_start:x_end, y_start:y_end] += prediction_classes[i, j]
            weight_matrix[x_start:x_end, y_start:y_end] += 1
    
    # Take average result
    prediction_result = (blended_prediction / weight_matrix).astype(np.float32)

    # Cut back any extra from patch overlap
    prediction_result = prediction_result[:tile_size, :tile_size]

    return prediction_result

# Function - Save tile
def save_tile(prediction, meta, filepath):
    """
    Write prediction output to GeoTIFF
    """
    # Update metadata (reduced band count from aerial)
    meta.update({
        "driver": "GTiff",
        "height": prediction.shape[0],
        "width": prediction.shape[0],
        "count": 1,
        "dtype": "uint8",
    })

    meta["crs"] = CRS.from_epsg(3857)

    # Save prediction
    prediction = np.expand_dims(prediction, axis=0)
    #print(prediction.shape)
    with rasterio.open(filepath, "w", **meta) as dst:
        dst.write(prediction)

def main():
    # Load Prediction Model
    try:
        model = load_model(PATH_MODEL)
    except Exception as e:
        print(f'Error loading model: {e}')

    # Load aerial tiles
    tiles = import_tiles()

    # Lazy load tile, predict, save and garbage collect
    stop_after = 2000
    for tile_image, meta, filename in tiles:
        if stop_after <= 0: break
        stop_after -= 1

        # Skip if already predicted
        print(f"Processing: {filename}")
        out_path = os.path.join(DIR_OUT_PREDICTIONS, f'pred_{filename}')
        if os.path.exists(out_path): 
            print('skip')
            continue

       # Predict
        prediction = predict_tile(model, tile_image)

        # Save
        save_tile(prediction, meta, out_path)
    
if __name__ == "__main__": main()
print("Execution complete")