<template>
  <div class="hex-tile-container">
    <canvas ref="hexCanvas" :width="width" :height="height" class="hex-canvas" @click="handleCanvasClick"></canvas>
    <div v-if="showDebug" class="debug-info">
      <h3>Tile Information</h3>
      <p><strong>Tile ID:</strong> {{ hexId }}</p>
      <p><strong>Resolution:</strong> {{ resolution }}</p>
      <p><strong>Content:</strong> {{ content || 'None' }}</p>
      <div class="visual-props">
        <p><strong>Visual Properties:</strong></p>
        <div class="color-samples">
          <div class="color-sample" :style="{ backgroundColor: fillColor }">
            <span>Fill</span>
          </div>
          <div class="color-sample" :style="{ backgroundColor: strokeColor }">
            <span>Border</span>
          </div>
        </div>
      </div>
      <div class="controls">
        <button @click="toggleNeighbors">{{ showNeighbors ? 'Hide' : 'Show' }} Neighbors</button>
      </div>
      <div v-if="selectedNeighbor" class="selected-info">
        <p><strong>Selected:</strong> {{ selectedNeighbor.substring(0, 6) }}...</p>
        <button @click="navigateToNeighbor" class="navigate-btn">Navigate to Selected</button>
      </div>
      <div v-if="errorMessage" class="error-message">
        <p><strong>Error:</strong> {{ errorMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import * as h3 from 'h3-js'

const props = defineProps({
  hexId: {
    type: String,
    default: '822837fffffffff' // Default to San Francisco at resolution 2
  },
  width: {
    type: Number,
    default: 800
  },
  height: {
    type: Number,
    default: 600
  },
  fillColor: {
    type: String,
    default: '#f0f0f0'
  },
  strokeColor: {
    type: String,
    default: '#ff0000'
  },
  strokeWidth: {
    type: Number,
    default: 3
  },
  content: {
    type: String,
    default: ''
  },
  showDebug: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['navigate'])

const hexCanvas = ref(null)
const centerX = ref(props.width / 2)
const centerY = ref(props.height / 2)
const hexSize = ref(Math.min(props.width, props.height) * 0.35)
const resolution = computed(() => {
  try {
    return h3.getResolution(props.hexId)
  } catch (e) {
    errorMessage.value = `Invalid H3 index: ${props.hexId}`
    return '?'
  }
})
const showNeighbors = ref(false)
const neighbors = ref([])
const neighborPositions = ref([])
const selectedNeighbor = ref(null)
const errorMessage = ref('')

// Calculate hexagon points
const calculateHexPoints = (center = { x: centerX.value, y: centerY.value }, size = hexSize.value) => {
  const points = []
  for (let i = 0; i < 6; i++) {
    // Start from the top point (270 degrees or -90 degrees) and go clockwise
    const angle = (Math.PI / 3) * i - Math.PI / 2
    const x = center.x + size * Math.cos(angle)
    const y = center.y + size * Math.sin(angle)
    points.push({ x, y })
  }
  return points
}

// Get neighboring hexagons
const getNeighbors = () => {
  errorMessage.value = '' // Clear previous errors
  try {
    // Get the neighbors using gridDisk with ringSize 1, then filter out the center cell
    const allCells = h3.gridDisk(props.hexId, 1)
    const neighborIndices = allCells.filter(id => id !== props.hexId)
    neighbors.value = neighborIndices
    
    // Calculate positions for neighbors
    neighborPositions.value = []
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i - Math.PI / 2
      const x = centerX.value + hexSize.value * 2 * Math.cos(angle)
      const y = centerY.value + hexSize.value * 2 * Math.sin(angle)
      // Only assign an ID if it exists in the neighborIndices array
      const neighborId = i < neighborIndices.length ? neighborIndices[i] : null
      neighborPositions.value.push({ x, y, id: neighborId })
    }
    
    return neighborIndices
  } catch (e) {
    console.error('Error getting neighbors:', e)
    errorMessage.value = `Error getting neighbors: ${e.message}`
    neighbors.value = []
    neighborPositions.value = []
    return []
  }
}

// Toggle showing neighbors
const toggleNeighbors = () => {
  showNeighbors.value = !showNeighbors.value
  if (showNeighbors.value) {
    getNeighbors()
  } else {
    selectedNeighbor.value = null
  }
  drawHexagon()
}

// Handle canvas click
const handleCanvasClick = (event) => {
  if (!showNeighbors.value) return
  
  const rect = hexCanvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  // Check if a neighbor was clicked
  for (let i = 0; i < neighborPositions.value.length; i++) {
    const neighbor = neighborPositions.value[i]
    if (!neighbor.id) continue
    
    const distance = Math.sqrt(
      Math.pow(x - neighbor.x, 2) + 
      Math.pow(y - neighbor.y, 2)
    )
    
    if (distance <= hexSize.value * 0.8) {
      selectedNeighbor.value = neighbor.id
      drawHexagon()
      return
    }
  }
  
  // If we get here, no neighbor was clicked
  selectedNeighbor.value = null
  drawHexagon()
}

// Navigate to the selected neighbor
const navigateToNeighbor = () => {
  if (selectedNeighbor.value) {
    emit('navigate', selectedNeighbor.value)
  }
}

// Draw the hexagon on the canvas
const drawHexagon = () => {
  errorMessage.value = '' // Clear previous errors
  const canvas = hexCanvas.value
  if (!canvas) {
    errorMessage.value = 'Canvas not available'
    return
  }
  
  try {
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, props.width, props.height)
    
    // Draw neighbors if enabled
    if (showNeighbors.value) {
      drawNeighbors(ctx)
    }
    
    // Draw main hexagon
    const points = calculateHexPoints()
    
    // Create clipping path (hexagon shape)
    ctx.beginPath()
    ctx.moveTo(points[0].x, points[0].y)
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y)
    }
    ctx.closePath()
    
    // Fill
    ctx.fillStyle = props.fillColor
    ctx.fill()
    
    // Draw grid pattern
    drawGridPattern(ctx, points)
    
    // Draw content text if available
    if (props.content) {
      ctx.fillStyle = '#333'
      ctx.font = '16px Arial'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(props.content, centerX.value, centerY.value)
    }
    
    // Draw the hexagon ID
    ctx.fillStyle = '#333'
    ctx.font = '12px monospace'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'
    ctx.fillText(props.hexId, centerX.value, centerY.value + hexSize.value * 0.8)
    
    // Stroke (border)
    ctx.strokeStyle = props.strokeColor
    ctx.lineWidth = props.strokeWidth
    ctx.stroke()
  } catch (e) {
    console.error('Error drawing hexagon:', e)
    errorMessage.value = `Failed to draw hexagon: ${e.message}`
  }
}

// Draw neighboring hexagons
const drawNeighbors = (ctx) => {
  const neighborIds = neighbors.value
  
  // Draw each neighbor
  neighborIds.forEach((id, index) => {
    if (index >= neighborPositions.value.length) return
    
    const pos = neighborPositions.value[index]
    if (!pos || !pos.id) return // Skip if position or ID is missing
    
    const points = calculateHexPoints({ x: pos.x, y: pos.y }, hexSize.value * 0.8)
    
    // Draw hexagon
    ctx.beginPath()
    ctx.moveTo(points[0].x, points[0].y)
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y)
    }
    ctx.closePath()
    
    // Fill with a lighter color or highlight if selected
    if (id === selectedNeighbor.value) {
      ctx.fillStyle = '#b3e5fc' // Light blue for selected neighbor
    } else {
      ctx.fillStyle = '#e0e0e0'
    }
    ctx.fill()
    
    // Draw simple grid
    drawSimpleGrid(ctx, points)
    
    // Draw ID
    ctx.fillStyle = '#666'
    ctx.font = '10px monospace'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(id.substring(0, 6) + '...', pos.x, pos.y)
    
    // Stroke with different color if selected
    if (id === selectedNeighbor.value) {
      ctx.strokeStyle = '#0288d1' // Darker blue for selected neighbor border
      ctx.lineWidth = 2
    } else {
      ctx.strokeStyle = '#999'
      ctx.lineWidth = 1
    }
    ctx.stroke()
  })
}

// Draw a simple grid pattern to simulate a map
const drawGridPattern = (ctx, points) => {
  // Save the current state
  ctx.save()
  
  // Create a clipping path for the hexagon
  ctx.beginPath()
  ctx.moveTo(points[0].x, points[0].y)
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y)
  }
  ctx.closePath()
  ctx.clip()
  
  // Draw grid lines
  ctx.strokeStyle = '#ccc'
  ctx.lineWidth = 1
  
  // Find the bounding box of the hexagon
  let minX = Math.min(...points.map(p => p.x))
  let maxX = Math.max(...points.map(p => p.x))
  let minY = Math.min(...points.map(p => p.y))
  let maxY = Math.max(...points.map(p => p.y))
  
  // Draw vertical lines
  const gridSize = 20
  for (let x = minX - (minX % gridSize); x <= maxX; x += gridSize) {
    ctx.beginPath()
    ctx.moveTo(x, minY)
    ctx.lineTo(x, maxY)
    ctx.stroke()
  }
  
  // Draw horizontal lines
  for (let y = minY - (minY % gridSize); y <= maxY; y += gridSize) {
    ctx.beginPath()
    ctx.moveTo(minX, y)
    ctx.lineTo(maxX, y)
    ctx.stroke()
  }
  
  // Restore the context
  ctx.restore()
}

// Draw a simpler grid for neighbors
const drawSimpleGrid = (ctx, points) => {
  ctx.save()
  
  // Create a clipping path
  ctx.beginPath()
  ctx.moveTo(points[0].x, points[0].y)
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y)
  }
  ctx.closePath()
  ctx.clip()
  
  // Draw simplified grid
  ctx.strokeStyle = '#ddd'
  ctx.lineWidth = 0.5
  
  // Find the bounding box
  let minX = Math.min(...points.map(p => p.x))
  let maxX = Math.max(...points.map(p => p.x))
  let minY = Math.min(...points.map(p => p.y))
  let maxY = Math.max(...points.map(p => p.y))
  
  // Draw fewer grid lines
  const gridSize = 30
  for (let x = minX - (minX % gridSize); x <= maxX; x += gridSize) {
    ctx.beginPath()
    ctx.moveTo(x, minY)
    ctx.lineTo(x, maxY)
    ctx.stroke()
  }
  
  for (let y = minY - (minY % gridSize); y <= maxY; y += gridSize) {
    ctx.beginPath()
    ctx.moveTo(minX, y)
    ctx.lineTo(maxX, y)
    ctx.stroke()
  }
  
  ctx.restore()
}

// Watch for changes to redraw
watch(() => props.hexId, () => {
  selectedNeighbor.value = null
  if (showNeighbors.value) {
    getNeighbors()
  }
  drawHexagon()
})
watch(() => props.width, drawHexagon)
watch(() => props.height, drawHexagon)
watch(() => props.fillColor, drawHexagon)
watch(() => props.strokeColor, drawHexagon)
watch(() => props.strokeWidth, drawHexagon)
watch(() => props.content, drawHexagon)
watch(() => showNeighbors.value, drawHexagon)

// Initialize on mount
onMounted(() => {
  console.log('HexTile mounted with ID:', props.hexId)
  getNeighbors()
  drawHexagon()
  
  // Handle window resize
  const handleResize = () => {
    if (hexCanvas.value) {
      centerX.value = hexCanvas.value.width / 2
      centerY.value = hexCanvas.value.height / 2
      hexSize.value = Math.min(hexCanvas.value.width, hexCanvas.value.height) * 0.35
      drawHexagon()
    }
  }
  
  window.addEventListener('resize', handleResize)
  
  // Clean up event listener on unmount
  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
  })
})

// Expose methods and properties
defineExpose({
  drawHexagon,
  calculateHexPoints,
  centerX,
  centerY,
  hexSize,
  toggleNeighbors,
  showNeighbors,
  neighbors,
  selectedNeighbor,
  navigateToNeighbor
})
</script>

<style scoped>
.hex-tile-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f5f5;
}

.hex-canvas {
  max-width: 100%;
  max-height: 100%;
  cursor: pointer;
}

.debug-info {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 15px;
  border-radius: 8px;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  max-width: 300px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.debug-info h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  color: #333;
}

.visual-props {
  margin-top: 10px;
}

.color-samples {
  display: flex;
  gap: 10px;
  margin-top: 5px;
}

.color-sample {
  width: 60px;
  height: 25px;
  border: 1px solid #ccc;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.color-sample span {
  background-color: rgba(255, 255, 255, 0.7);
  padding: 2px 5px;
  border-radius: 3px;
  font-size: 10px;
}

.controls {
  margin-top: 15px;
  display: flex;
  justify-content: center;
}

.controls button, .navigate-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.3s;
}

.controls button:hover, .navigate-btn:hover {
  background-color: #45a049;
}

.selected-info {
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
  text-align: center;
}

.navigate-btn {
  background-color: #2196F3;
  margin-top: 5px;
}

.navigate-btn:hover {
  background-color: #0b7dda;
}

.error-message {
  margin-top: 15px;
  padding: 10px;
  background-color: #ffebee;
  border-left: 4px solid #f44336;
  border-radius: 4px;
}

.error-message p {
  margin: 0;
  color: #d32f2f;
  font-size: 12px;
}
</style>
