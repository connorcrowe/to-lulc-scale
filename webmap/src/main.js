import L from "leaflet";
import "leaflet/dist/leaflet.css";
import GeoRasterLayer from "georaster-layer-for-leaflet";
import georaster from "georaster";
import { Map, TileLayer, ImageOverlay, CRS } from 'leaflet';

// Initialize the map
// Initialize map
const map = new Map('map', {
  center: [43.7, -79.42], // Center on Toronto
  zoom: 12,
  crs: CRS.EPSG3857, 
});

// Add base layer
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
}).addTo(map);

// Load and display the COG
fetch("public/pred_tile_-8812983_5429619.tif")
  .then((response) => response.arrayBuffer())
  .then((arrayBuffer) => {
    console.log("Loaded ArrayBuffer, parsing with georaster...");
    return georaster(arrayBuffer);
  })
  .then((raster) => {
    console.log("Parsed raster:", raster); 

    // const layer = new GeoRasterLayer({
    //   georaster: raster,
    //   opacity: 0.7,
    //   resolution: 256,
    // });

    const layer = new GeoRasterLayer({
      georaster: raster,
      opacity: 0.5,
      resolution: 256,
      pixelValuesToColorFn: (values) => {
        const val = values[0]; // Assume single-band classification
        if (val === 0) return "#20806f"; // road
        if (val === 1) return "#dcdcdc"; // pavement
        if (val === 2) return "#c59864"; // building
        if (val === 3) return "#609b61"; // vegetation
        if (val === 4) return "#4e88ca"; // water
        return "#00000000"; // transparent for nodata or unknown
      },
    });

    layer.addTo(map);
    map.fitBounds(layer.getBounds());
  })
  .catch((err) => console.error("Error loading COG:", err));


  /*
        if (val === 0) return "#20806f"; // road
        if (val === 1) return "#dcdcdc"; // pavement
        if (val === 2) return "#c59864"; // building
        if (val === 3) return "#609b61"; // vegetation
        if (val === 4) return "#4e88ca"; // water
  */