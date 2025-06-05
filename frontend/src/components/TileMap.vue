<template>
  <div class="tile-map">
    <div id="map" ref="mapContainer"></div>
    <div class="active-tile-info" v-if="activeTile">
      <h3>Active Tile: {{ activeTile.id }}</h3>
      <p>{{ activeTile.content || 'No content' }}</p>
    </div>
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
import * as h3 from 'h3-js'
import axios from 'axios'

// Base API URL
const API_BASE_URL = 'http://localhost:8000/api'

const router = useRouter()
const mapContainer = ref(null)
const map = ref(null)
const activeTile = ref(null)
const tileLayer = ref(null)
const hexLayer = ref(null)
const error = ref(null)

// Use the center tile ID from our sample data
const centerTileId = '822837fffffffff'
const defaultZoom = 2

// Initialize the map
const initMap = () => {
  try {
    // Create the Leaflet map
    map.value = L.map(mapContainer.value, {
      center: [37.7749, -122.4194], // San Francisco coordinates
      zoom: defaultZoom,
      zoomControl: true,
      attributionControl: true
    })
    
    // Add OpenStreetMap tile layer
    tileLayer.value = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map.value)
    
    // Create a layer for hexagons
    hexLayer.value = L.layerGroup().addTo(map.value)
    
    // Generate initial hexagons
    generateHexagons(centerTileId)
  } catch (e) {
    console.error("Error initializing map:", e)
    error.value = `Error initializing map: ${e.message}`
  }
}

// Generate hexagons around a center tile ID
const generateHexagons = async (centerIndex) => {
  try {
    // Clear existing hexagons
    if (hexLayer.value) {
      hexLayer.value.clearLayers()
    }
    
    // Get the active tile data
    const response = await axios.get(`${API_BASE_URL}/tiles/${centerIndex}`)
    activeTile.value = response.data
    
    // Add the center hexagon
    addHexagonToMap(centerIndex, true)
    
    // Get and add neighboring hexagons
    const neighborsResponse = await axios.get(`${API_BASE_URL}/tiles/${centerIndex}/neighbors`)
    const neighbors = neighborsResponse.data.neighbors
    
    neighbors.forEach(neighbor => {
      addHexagonToMap(neighbor.id, false)
    })
    
    // Center the map on the active hexagon
    try {
      const boundary = h3.cellToBoundary(centerIndex, true)
      const center = h3.cellToLatLng(centerIndex)
      map.value.setView([center[0], center[1]], defaultZoom)
    } catch (e) {
      console.error("Error centering map:", e)
    }
  } catch (e) {
    console.error('Error generating hexagons:', e)
    error.value = `Error loading tile data: ${e.message}`
  }
}

// Add a hexagon to the map
const addHexagonToMap = (h3Index, isActive) => {
  try {
    // Get the boundary of the hexagon
    const boundary = h3.cellToBoundary(h3Index, true)
    
    // Convert to Leaflet format
    const latlngs = boundary.map(point => [point[0], point[1]])
    
    // Create polygon
    const polygon = L.polygon(latlngs, {
      color: isActive ? '#FF0000' : '#3388ff',
      weight: isActive ? 3 : 1,
      fillColor: isActive ? '#FFA500' : '#3388ff',
      fillOpacity: isActive ? 0.4 : 0.2
    })
    
    // Add click handler
    polygon.on('click', () => {
      router.push({ name: 'tile', params: { id: h3Index } })
    })
    
    // Add tooltip
    polygon.bindTooltip(h3Index)
    
    // Add to layer
    hexLayer.value.addLayer(polygon)
  } catch (e) {
    console.error(`Error adding hexagon ${h3Index} to map:`, e)
  }
}

// Lifecycle hooks
onMounted(() => {
  // Add a small delay to ensure the container is fully rendered
  setTimeout(() => {
    initMap()
  }, 100)
})

onUnmounted(() => {
  if (map.value) {
    map.value.remove()
  }
})
</script>

<style scoped>
.tile-map {
  position: relative;
  width: 100%;
  height: 100%;
}

#map {
  width: 100%;
  height: 100%;
}

.active-tile-info {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background-color: white;
  border-radius: 4px;
  padding: 10px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  max-width: 300px;
  z-index: 1000;
}

.error-message {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #ff6b6b;
  color: white;
  padding: 10px 20px;
  border-radius: 4px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}
</style>
