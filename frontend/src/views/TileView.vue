<template>
  <div class="tile-view">
    <div class="active-tile">
      <h2>Tile: {{ tileId }}</h2>
      <div v-if="tile" class="tile-content">
        <p><strong>Content:</strong> {{ tile.content || 'No content' }}</p>
        <div class="tile-properties">
          <h3>Visual Properties</h3>
          <div class="property" v-for="(value, key) in tile.visual_properties" :key="key">
            <span>{{ key }}:</span> <span>{{ value }}</span>
          </div>
        </div>
      </div>
      <div v-else class="loading">Loading tile data...</div>
    </div>
    <div class="neighbors">
      <h3>Neighboring Tiles</h3>
      <div v-if="neighbors.length" class="neighbor-list">
        <div 
          v-for="neighbor in neighbors" 
          :key="neighbor.id" 
          class="neighbor-tile"
          @click="navigateToTile(neighbor.id)"
        >
          {{ neighbor.id }}
        </div>
      </div>
      <div v-else class="loading">Loading neighbors...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

// Base API URL
const API_BASE_URL = 'http://localhost:8000/api'

const route = useRoute()
const router = useRouter()
const tileId = ref(route.params.id)
const tile = ref(null)
const neighbors = ref([])

// Watch for route changes to update the tile ID
watch(() => route.params.id, (newId) => {
  tileId.value = newId
  fetchTileData()
  fetchNeighbors()
})

// Fetch tile data from the API
const fetchTileData = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tiles/${tileId.value}`)
    tile.value = response.data
  } catch (error) {
    console.error('Error fetching tile data:', error)
  }
}

// Fetch neighboring tiles
const fetchNeighbors = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tiles/${tileId.value}/neighbors`)
    neighbors.value = response.data.neighbors
  } catch (error) {
    console.error('Error fetching neighbors:', error)
  }
}

// Navigate to another tile
const navigateToTile = (id) => {
  router.push({ name: 'tile', params: { id } })
}

// Fetch data when component is mounted
onMounted(() => {
  fetchTileData()
  fetchNeighbors()
})
</script>

<style scoped>
.tile-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1rem;
}

.active-tile {
  flex: 3;
  background-color: #f5f5f5;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.neighbors {
  flex: 1;
  background-color: #f5f5f5;
  border-radius: 8px;
  padding: 1rem;
}

.neighbor-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.neighbor-tile {
  background-color: #e0e0e0;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 0.5rem;
  cursor: pointer;
  font-size: 0.8rem;
  transition: background-color 0.2s;
}

.neighbor-tile:hover {
  background-color: #d0d0d0;
}

.loading {
  color: #666;
  font-style: italic;
}

.tile-properties {
  margin-top: 1rem;
}

.property {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
  border-bottom: 1px solid #eee;
}
</style>
