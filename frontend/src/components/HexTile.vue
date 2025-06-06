<template>
  <div class="hex-tile-container">
    <canvas ref="hexCanvas" :width="width" :height="height" class="hex-canvas" @click="handleCanvasClick"></canvas>
    <div v-if="errorMessage" class="error-message">
      <p><strong>Error:</strong> {{ errorMessage }}</p>
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
  }
})

const emit = defineEmits(['navigate', 'selectNeighbor'])

const hexCanvas = ref(null)
const centerX = ref(props.width / 2)
const centerY = ref(props.height / 2)
const hexSize = ref(Math.min(props.width, props.height) * 0.45)
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
    
    // Calculate positions for neighbors using a simpler approach
    neighborPositions.value = []
    
    // Use a fixed distance and angles for neighbor positions
    // This is a simplified approach that ensures neighbors are visible
    const neighborCount = neighborIndices.length
    
    for (let i = 0; i < neighborCount; i++) {
      // Calculate position in a hexagonal pattern around the center
      const angle = (Math.PI * 2 * i) / neighborCount
      const distance = hexSize.value * 1.7
      
      const x = centerX.value + Math.cos(angle) * distance
      const y = centerY.value + Math.sin(angle) * distance
      
      neighborPositions.value.push({ 
        x, 
        y, 
        id: neighborIndices[i] 
      })
    }
    
    console.log(`Found ${neighborIndices.length} neighbors, created ${neighborPositions.value.length} positions`)
    
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
    emit('selectNeighbor', null)
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
      emit('selectNeighbor', neighbor.id)
      drawHexagon()
      return
    }
  }
  
  // If we get here, no neighbor was clicked
  selectedNeighbor.value = null
  emit('selectNeighbor', null)
  drawHexagon()
}

// Navigate to the selected neighbor
const navigateToNeighbor = () => {
  if (selectedNeighbor.value) {
    emit('navigate', selectedNeighbor.value)
  }
}

// Draw a single hexagon with the given parameters
const drawSingleHexagon = (ctx, center, size, fillColor, strokeColor, strokeWidth, content, id, isSelected = false) => {
  const points = calculateHexPoints(center, size)
  
  // Create path (hexagon shape)
  ctx.beginPath()
  ctx.moveTo(points[0].x, points[0].y)
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y)
  }
  ctx.closePath()
  
  // Fill
  ctx.fillStyle = fillColor
  ctx.fill()
  
  // Use the same grid pattern for all hexagons
  drawGridPattern(ctx, points)
  
  // Draw content text if available
  if (content) {
    ctx.fillStyle = '#333'
    ctx.font = '16px Arial'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(content, center.x, center.y)
  }
  
  // Draw the hexagon ID
  ctx.fillStyle = '#333'
  ctx.font = isSelected ? '12px monospace' : '10px monospace'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'bottom'
  ctx.fillText(id.substring(0, 6) + (isSelected ? '' : '...'), center.x, center.y + size * 0.6)
  
  // Stroke (border)
  ctx.beginPath()
  ctx.moveTo(points[0].x, points[0].y)
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y)
  }
  ctx.closePath()
  ctx.strokeStyle = strokeColor
  ctx.lineWidth = strokeWidth
  ctx.stroke()
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
    
    // Draw main hexagon using the reusable function
    drawSingleHexagon(
      ctx,
      { x: centerX.value, y: centerY.value },
      hexSize.value,
      props.fillColor,
      props.strokeColor,
      props.strokeWidth,
      props.content,
      props.hexId,
      true
    )
    
  } catch (e) {
    console.error('Error drawing hexagon:', e)
    errorMessage.value = `Failed to draw hexagon: ${e.message}`
  }
}

// Draw neighboring hexagons
const drawNeighbors = (ctx) => {
  const neighborIds = neighbors.value
  
  // Draw each neighbor using the reusable function
  neighborIds.forEach((id, index) => {
    if (index >= neighborPositions.value.length) return
    
    const pos = neighborPositions.value[index]
    if (!pos || !pos.id) return // Skip if position or ID is missing
    
    // Use the same styling as the main hexagon, just highlight selected ones
    const fillColor = id === selectedNeighbor.value ? '#b3e5fc' : props.fillColor
    const strokeColor = id === selectedNeighbor.value ? '#0288d1' : props.strokeColor
    const strokeWidth = id === selectedNeighbor.value ? props.strokeWidth : props.strokeWidth
    
    // Draw the neighbor hexagon using the reusable function
    drawSingleHexagon(
      ctx,
      { x: pos.x, y: pos.y },
      hexSize.value, // Same size as the main hexagon
      fillColor,
      strokeColor,
      strokeWidth,
      '', // No content for neighbors
      id,
      id === selectedNeighbor.value
    )
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
      const canvasWidth = props.width
      const canvasHeight = props.height
      
      hexCanvas.value.width = canvasWidth
      hexCanvas.value.height = canvasHeight
      
      centerX.value = canvasWidth / 2
      centerY.value = canvasHeight / 2
      hexSize.value = Math.min(canvasWidth, canvasHeight) * 0.45
      
      if (showNeighbors.value) {
        getNeighbors()
      }
      
      drawHexagon()
    }
  }
  
  window.addEventListener('resize', handleResize)
  
  // Clean up event listener on unmount
  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
  })
})

// Expose methods and data for parent component
defineExpose({
  toggleNeighbors,
  navigateToNeighbor,
  resolution,
  showNeighbors,
  selectedNeighbor
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

.error-message {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background-color: rgba(255, 0, 0, 0.8);
  color: white;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 14px;
  z-index: 100;
}
</style>
