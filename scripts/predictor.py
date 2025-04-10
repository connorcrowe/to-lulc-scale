# Imports
import tensorflow.keras.backend as K
from tensorflow.keras.models import load_model

# Set directories
DIR_IN_TILES = 'data/tiles/'
DIR_OUT_PREDICTIONS = 'data/predictions/'



# Function - Import tile
def import_tile():
    """
    Loads an aerial tile to be predicted
    """

# Function - Predict tile
def predict_tile(tile):
    """
    Runs LULC model on a single tile
    """

# Function - Save tile
def save_tile(tile):
    """
    Write prediction output to GeoTIFF
    """

# Main Loop
def main():

    # Load Prediction Model
    model_path = 'model/unet_model_512pd_4layer_batch_drop_5deepkernel.keras'
    try:
        model = load_model(model_path)
    except Exception as e:
        print(f'Error loading model: {e}')

    # Import
    tile = import_tile()

    # Predict
    prediction = predict_tile(tile)

    # Save
    save_tile(prediction)

    # Garbage Collect

if __name__ == "__main__": main()
print("Execution complete")