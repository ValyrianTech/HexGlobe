<template>
  <div class="tile-navigation">
    <div class="neighbors-container">
      <Tile 
        v-for="neighbor in neighbors" 
        :key="neighbor.id"
        :id="neighbor.id"
        :content="neighbor.content"
        :visual-properties="neighbor.visual_properties || defaultVisualProps"
        @click="navigateToTile(neighbor.id)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import Tile from './Tile.vue'

const props = defineProps({
  tileId: {
    type: String,
    required: true
  }
})

const route = useRoute()
const router = useRouter()
const neighbors = ref([])
const defaultVisualProps = {
  borderColor: '#000000',
  borderThickness: 1,
  borderStyle: 'solid',
  fillColor: '#f0f0f0'
}

// Watch for tile ID changes
watch(() => props.tileId, (newId) => {
  if (newId) {
    fetchNeighbors(newId)
  }
})

// Fetch neighboring tiles
const fetchNeighbors = async (id) => {
  try {
    const response = await axios.get(`http://localhost:8000/api/tiles/${id}/neighbors`)
    neighbors.value = response.data.neighbors
    
    // Fetch content for each neighbor
    for (const neighbor of neighbors.value) {
      try {
        const tileResponse = await axios.get(`http://localhost:8000/api/tiles/${neighbor.id}`)
        neighbor.content = tileResponse.data.content
        neighbor.visual_properties = tileResponse.data.visual_properties
      } catch (error) {
        console.error(`Error fetching data for tile ${neighbor.id}:`, error)
      }
    }
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
  if (props.tileId) {
    fetchNeighbors(props.tileId)
  }
})
</script>

<style scoped>
.tile-navigation {
  padding: 1rem;
}

.neighbors-container {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
}
</style>
