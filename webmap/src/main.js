import L from "leaflet";
import "leaflet/dist/leaflet.css";
import * as esri from "esri-leaflet";

// Initialize the map
const map = L.map("map", {
  center: [43.7, -79.42], // Centered on Toronto
  zoom: 13,
  minZoom: 12,
  maxZoom: 16,
});

// Add base map layer
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
}).addTo(map);

// Add aerial imagery from Toronto MapServer
const aerialLayer = esri.tiledMapLayer({
  url: "https://gis.toronto.ca/arcgis/rest/services/basemap/cot_ortho_2023_color_10cm/MapServer",
  attribution: "City of Toronto Aerial Imagery 2023",
}).addTo(map);

// Add prediction tiles layer
const predictionLayer = L.tileLayer("tiles/{z}/{x}/{y}.png", {
  tms: true, 
  attribution: "LULC Predictions",
  opacity: 0.9,
}).addTo(map);


// Toggle Prediction Layer
const predToggle = document.getElementById("toggle-prediction");
let predVisible = true;
predToggle.addEventListener("click", () => {
  if (predVisible) {
    map.removeLayer(predictionLayer);
  } else {
    map.addLayer(predictionLayer);
  }
  predVisible = !predVisible;
});

// Toggle Aerial Layer
const aerialToggle = document.getElementById("toggle-aerial");
let aerialVisible = false;
aerialToggle.addEventListener("click", () => {
  if (aerialVisible) {
    map.removeLayer(aerialLayer);
  } else {
    map.addLayer(aerialLayer);
  }
  aerialVisible = !aerialVisible;
});