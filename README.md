# to-lulc-scale
**Objective**: Using the model trained in #to-lulc-aiml, predict the land use land cover classification of the entire City of Toronto

**Details**:
- Slice the 2024 aerial image into tiles from it's WMS
- Predict LULC on tiles systematically (likely locally for cost savings)
- Post-process to smooth tile edges
- Collate and display results on web mapping service

**Rough, Initial ToDo**:
- ✅ Using python, get a specific extent of the WMS aerial at a specific resolution
- Design slicing algorithm 
- Determine result storage
- Begin predicting slices
- Design post-processing algorithm
- Determine webmap hosting solution

**Structure**:
to-lulc-scale/
|-- data/               # WMS tiles and predicted tiles
|-- model/              # Trained models
|-- scripts/
|   |-- slicer.py       # Slice WMS into tiles
|   |-- predictor.py    # Predict lulc on slices
|   |-- processor.py    # Convert predictions for display
|-- webmap/             # For visualising results 
|-- notebooks/          # Experiments & testing