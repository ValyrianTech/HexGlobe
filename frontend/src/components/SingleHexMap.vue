<template>
  <div class="single-hex-map">
    <div id="map" ref="mapContainer"></div>
    <div v-if="hexInfo" class="hex-info">
      <h3>Hexagon Info</h3>
      <p><strong>ID:</strong> {{ hexInfo.id }}</p>
      <p><strong>Center:</strong> {{ hexInfo.center.join(', ') }}</p>
      <p><strong>Resolution:</strong> {{ hexInfo.resolution }}</p>
    </div>
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import * as h3 from 'h3-js'

const mapContainer = ref(null)
const map = ref(null)
const error = ref(null)
const hexInfo = ref(null)

// San Francisco center hex at resolution 2
const centerHexId = '822837fffffffff'

onMounted(() => {
  console.log('SingleHexMap component mounted')
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

const initMap = () => {
  try {
    console.log('Initializing map with hex ID:', centerHexId)
    
    // Get the center coordinates of the hex
    const centerCoords = h3.cellToLatLng(centerHexId)
    console.log('Center coordinates:', centerCoords)
    
    // Create the Leaflet map
    map.value = L.map(mapContainer.value, {
      center: [centerCoords[0], centerCoords[1]],
      zoom: 5, // Closer zoom to see the hexagon better
      zoomControl: true,
      attributionControl: true
    })
    
    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map.value)
    
    // Draw the hexagon
    drawHexagon(centerHexId)
    
    // Store hex info for display
    hexInfo.value = {
      id: centerHexId,
      center: centerCoords,
      resolution: h3.getResolution(centerHexId)
    }
    
    console.log('Map initialized with hexagon:', centerHexId)
  } catch (e) {
    console.error('Error initializing map:', e)
    error.value = `Error initializing map: ${e.message}`
  }
}

const drawHexagon = (hexId) => {
  try {
    // Get the boundary of the hexagon
    const boundary = h3.cellToBoundary(hexId, true)
    console.log('Hexagon boundary:', boundary)
    
    // Convert to Leaflet format
    const latlngs = boundary.map(point => [point[0], point[1]])
    
    // Create polygon with a semi-transparent fill
    const polygon = L.polygon(latlngs, {
      color: '#FF0000',
      weight: 2,
      fillColor: '#FFA500',
      fillOpacity: 0.3
    }).addTo(map.value)
    
    // Add tooltip with hex ID
    polygon.bindTooltip(hexId)
    
    // Add a marker at the center for reference
    const center = h3.cellToLatLng(hexId)
    L.marker([center[0], center[1]])
      .addTo(map.value)
      .bindTooltip('Center')
    
    // Fit the map to the hexagon bounds
    map.value.fitBounds(polygon.getBounds())
  } catch (e) {
    console.error(`Error drawing hexagon ${hexId}:`, e)
    error.value = `Error drawing hexagon: ${e.message}`
  }
}
</script>

<style scoped>
.single-hex-map {
  position: relative;
  width: 100%;
  height: 100%;
}

#map {
  width: 100%;
  height: 100%;
}

.hex-info {
  position: absolute;
  top: 20px;
  right: 20px;
  background-color: white;
  border-radius: 4px;
  padding: 10px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  max-width: 300px;
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
