<template>
  <div class="hexagon-container">
    <canvas ref="hexCanvas" :width="width" :height="height" class="hexagon-canvas"></canvas>
    <div v-if="showDebug" class="debug-info">
      <p><strong>Hexagon ID:</strong> {{ hexId }}</p>
      <p><strong>Resolution:</strong> {{ resolution }}</p>
      <p><strong>Center:</strong> ({{ centerX.toFixed(2) }}, {{ centerY.toFixed(2) }})</p>
      <p><strong>Size:</strong> {{ hexSize }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
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
  showDebug: {
    type: Boolean,
    default: true
  }
})

const hexCanvas = ref(null)
const centerX = ref(props.width / 2)
const centerY = ref(props.height / 2)
const hexSize = ref(Math.min(props.width, props.height) * 0.4)
const resolution = computed(() => h3.getResolution(props.hexId))

// Calculate hexagon points
const calculateHexPoints = () => {
  const points = []
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i
    const x = centerX.value + hexSize.value * Math.cos(angle)
    const y = centerY.value + hexSize.value * Math.sin(angle)
    points.push({ x, y })
  }
  return points
}

// Draw the hexagon on the canvas
const drawHexagon = () => {
  const canvas = hexCanvas.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, props.width, props.height)
  
  const points = calculateHexPoints()
  
  // Draw the hexagon
  ctx.beginPath()
  ctx.moveTo(points[0].x, points[0].y)
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y)
  }
  ctx.closePath()
  
  // Fill
  ctx.fillStyle = props.fillColor
  ctx.fill()
  
  // Stroke
  ctx.strokeStyle = props.strokeColor
  ctx.lineWidth = props.strokeWidth
  ctx.stroke()
  
  // Draw the hexagon ID in the center
  ctx.fillStyle = '#333'
  ctx.font = '14px monospace'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(props.hexId, centerX.value, centerY.value)
}

// Watch for changes to redraw
watch(() => props.hexId, drawHexagon)
watch(() => props.width, drawHexagon)
watch(() => props.height, drawHexagon)
watch(() => props.fillColor, drawHexagon)
watch(() => props.strokeColor, drawHexagon)
watch(() => props.strokeWidth, drawHexagon)

// Initialize on mount
onMounted(() => {
  console.log('Canvas Hexagon mounted with ID:', props.hexId)
  drawHexagon()
})

// Expose methods and properties
defineExpose({
  drawHexagon,
  calculateHexPoints,
  centerX,
  centerY,
  hexSize
})
</script>

<style scoped>
.hexagon-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f5f5;
}

.hexagon-canvas {
  max-width: 100%;
  max-height: 100%;
}

.debug-info {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 10px;
  border-radius: 5px;
  font-family: monospace;
  max-width: 300px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}
</style>
