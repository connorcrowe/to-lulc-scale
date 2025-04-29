# Automatic high-res land use classification of the entire City of Toronto using a custom deep learning model.
**See the Live Demo**: [Web Demo](https://connorcrowe.github.io/to-lulc-scale/)

**Objective**: *Predict land use land cover (LULC) classification from aerial imagery for the entire City of Toronto area. Specific focus on handling, predicting, and displaying large geospatial data sources with constrained hardware.*

## Overview
This project uses a custom trained U-Net CNN model (made in **[#to-lulc-aiml](https://github.com/connorcrowe/to-lulc-aiml)**) to classify LULC for the entire City of Toronto from high resolution aerial imagery. LULC is a critical tool for urban planning & climate monitoring, but takes significant time and resources to do manually at a large scale. 

An automated approach can significantly reduce the resources required to have accurate and up to date LULC, allowing for more proactive planning.

There are some challenges with dealing with the amount of data required to map an entire city on limited hardware. For this project, automated scripts were created to create smaller tiles of the original aerial image of Toronto, run AI prediction on them, and then post-process them into workable results. Additionally, the resulting predictions must be tiled (with different resolutions at different zoom levels) to display effectively on a web demo. The challenges of scale were the primary learning objective of this project.

**Data sources**
- [City of Toronto ArcGIS REST Services Directory](https://gis.toronto.ca/arcgis/rest/services/basemap/cot_ortho_2023_color_10cm/MapServer) - 2023 Aerial imagery for model training and prediction

## Components
**Slicer**
- The slicer accesses the City of Toronto ArcGIS API and requests a specific area of the overall aerial
- This is set to a specific size (352 x 352 meters) and resolution (704 x 704 pixels) at specific coordinates
    - It is important to get the same spatial resolution for all tiles, and that it matches the spatial resolution of the training set
    - The CRS of ESPG:3857 was used since it was native to the API and allowed for simpler spatial indexing

**Predictor**
- The predictor script checks for aerial tiles and slices them into overlapping patches that match the input shape for model
- Then the prediction model is run on the tiles, and the overlapping areas are blended

**Processing**
- The 12,000+ tiles needed to be merged into a large GeoTIFF
- The merged result was colourized (from discrete class labels to colours for the map)
- GDAL was used to turn the colourized GeoTIFF into displayable image tiles with various zoom levels

**WebMap**
- A Vite web app was created to display the results in a live demo
- Leaflet was used to display the tiles of the predictions effectively
- The prediction is tiled with GDAL so as to have different resolutions at different zoom levels

## Model
The classifier is a u-net convolutional neural network trained on manually labelled training aerial images of Toronto. 
More info about how the model was built and other models explored here **[#to-lulc-aiml](https://github.com/connorcrowe/to-lulc-aiml)**.

**Training**
- Trained on 128x128 pixel, 64x64 meter overlapping aerials 
- Significant data augmentation to expand training set
- 5 Classes (road, pavement, building, vegetation, water)

**Architecture**
- 4 Layer U-Net 
- 4 convolutional layers, a bottleneck, and 4 up-convolutional layers with skip connections

## Results
**View the results on the [Web Demo](https://connorcrowe.github.io/to-lulc-scale/)**
The entire City of Toronto area was successfully sliced, predicted, merged and displayed. 

**Issues**
- In slicing, some aerial squares weren't returned properly, leaving gaps
- Not enough "deep water" was shown in training, causing unexpected classification in those areas
- No large highways were included in training - the model seems to clearly identify large expressways properly, but mislabels them as buildings
- High confusion of roads with buildings

**Strengths**
- Strong classification of roads and buildings in grid row home areas
- Parks and pavement paths in parks
- Breakwaters & most water
- Most smaller building structures

## Learning
- **Spatial Resolution** | It is important to work in a consistent pixels per meter across training, fitting and predicting since the model learns spatial relationships at a specific spatial resolution. Perhaps a more generalized model trained on varied resolutions would perform better, but a model trained on a specific spatial resolution does not predict other resolutions well.
- **CRS Differences** | Some coordinate systems index in latitude and longitude directly, others are projected in a way that indexes in meters. Keeping a consistent CRS across training and predicted is required for good performance.

## Future Work
- Automated post processing pipeline
- Fill in missing aerials
- Add highways & deep water to training set and retrain model

## Appendices 
**Running**:

**Repo Structure**:
```
to-lulc-scale/
|-- data/               # WMS tiles and predicted tiles
|-- model/              # Trained models
|-- scripts/
|   |-- slicer.py       # Slice WMS into tiles
|   |-- predictor.py    # Predict lulc on slices
|-- webmap/             # For visualising results 
|-- notebooks/          # Experiments & testing
```