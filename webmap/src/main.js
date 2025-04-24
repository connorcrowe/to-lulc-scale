import L from "leaflet";
import "leaflet/dist/leaflet.css";

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

// Add prediction tiles layer
const predictionLayer = L.tileLayer("tiles_colour/{z}/{x}/{y}.png", {
  tms: true, 
  attribution: "LULC Predictions",
  opacity: 0.9,
}).addTo(map);

// Toggle logic
const toggleButton = document.getElementById("toggle-prediction");
toggleButton.addEventListener("click", () => {
  if (map.hasLayer(predictionLayer)) {
    map.removeLayer(predictionLayer);
    toggleButton.textContent = "Show Prediction";
  } else {
    map.addLayer(predictionLayer);
    toggleButton.textContent = "Hide Prediction";
  }
});