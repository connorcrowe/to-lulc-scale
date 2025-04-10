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
from patchify import patchify
from patchify import unpatchify

# Set directories
DIR_IN_TILES = 'data/tiles/'
DIR_OUT_PREDICTIONS = 'data/predictions/'

# Set classification model
PATH_MODEL = 'model/unet_model_512pd_4layer_batch_drop_5deepkernel.keras'

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
    tile_reshaped = reshape_as_image(tile)                                              #  (512, 512, 3)

    # Split into patches of model input size to predict (128 x 128)
    patch_size = 128
    patch_step = 128
    patches = patchify(tile_reshaped, (patch_size, patch_size, 3), step = patch_step)   # (4, 4, 128, 128, 3)

    # Flatten to one list of patch_size x patch_size patches
    patches_reshaped = patches.reshape(-1, patch_size, patch_size, 3)                   # (16, 128, 128, 3)
    
    # Predict patches
    prediction = model.predict(patches_reshaped)                                        # (16, 128, 128, 5)
    
    # Unpatchify back to original shape
    prediction_reshaped = prediction.reshape(
        patches.shape[0], patches.shape[0], 1, patch_size, patch_size, 5)               # (4, 4, 1, 128, 128, 5)
    prediction_unpatched = unpatchify(prediction_reshaped, (512, 512, 5))               # (512, 512, 5)

    # Collapse to highest likelihood class for each pixel
    prediction_classes = np.argmax(prediction_unpatched, axis=-1)                       # (512, 512)
    
    return prediction_classes

# Function - Save tile
def save_tile(prediction, meta, tile_filename):
    """
    Write prediction output to GeoTIFF
    """
    # Set filepath
    pred_filename = f'pred_{tile_filename}'
    filepath = os.path.join(DIR_OUT_PREDICTIONS, pred_filename)

    # Update metadata (reduced band count from aerial)
    meta.update({
        'count': 1,
        'dtype': 'uint8'
    })

    # Save prediction
    prediction = np.expand_dims(prediction, axis=0)
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
    stop_after = 100
    skip = 60
    for tile_image, meta, filename in tiles:
        if skip >= 0: 
            skip -= 1
            continue
        if stop_after <= 0: break
        stop_after -= 1

        print(f"Processing: {filename}")

       # Predict
        prediction = predict_tile(model, tile_image)

        # Save
        save_tile(prediction, meta, filename)
    # Garbage Collect
    
if __name__ == "__main__": main()
print("Execution complete")