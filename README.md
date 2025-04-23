# to-lulc-scale
**Demo**: TBA

**Objective**: Using the U-Net CNN classifier trained in [to-lulc-aiml](https://github.com/connorcrowe/to-lulc-aiml), predict the land use land cover of the entire City of Toronto

## Project Overview
This project aimed to predict the LULC of a massive area, to test the limits of the model previously worked on, and to develop the ability to work with larger geospatial data pipelines. 

## Pipeline
**Aerial Tiles**
A python script was written to slice a 2023 aerial image of Toronto into 352 x 352 meter tiles. 

**Predictions**
A script then ran the U-Net predictor on the tiles. Each tile was split into overlapping patches with results weighted so as to reduce border artifacts within tiles.
- 5 Classes (road, pavement, building, vegetation, water)

**Processing**
The 12,088 prediction tiles in GeoTIFF format were merged with GDAL into a single GeoTIFF. Since this file was far to large to work with effectively (22GB) it was then converted with GDAL into a Cloud-Optimized-GeoTIFF (COG). Since the resulting COG was still too large for the memory buffer in the web demo, it was split into tiles with `gdal2tiles.py` so it could be displayed at various resolutions in the demo without requiring the entire image be loaded at once.

**Display**
A simple Vite web app was setup so that the results could be displayed with Leaflet. The tiles allow for different resolutions at different zoom levels, allowing for high resolution while zoomed in.

**Structure**:
to-lulc-scale/
|-- data/               # WMS tiles and predicted tiles
|-- model/              # Trained models
|-- scripts/
|   |-- slicer.py       # Slice WMS into tiles
|   |-- predictor.py    # Predict lulc on slices
|-- webmap/             # For visualising results 
|-- notebooks/          # Experiments & testing