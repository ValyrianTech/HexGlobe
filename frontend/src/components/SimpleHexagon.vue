<template>
  <div class="hexagon-container">
    <svg :width="width" :height="height" class="hexagon-svg">
      <polygon :points="hexPoints" class="hexagon" :style="hexagonStyle" />
      <text v-if="showCoordinates" x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" class="coordinate-text">
        {{ hexId }}
      </text>
    </svg>
    <div v-if="showDebug" class="debug-info">
      <p><strong>Hexagon ID:</strong> {{ hexId }}</p>
      <p><strong>Center:</strong> ({{ center.x.toFixed(2) }}, {{ center.y.toFixed(2) }})</p>
      <p><strong>Size:</strong> {{ hexSize }}</p>
      <p><strong>Points:</strong></p>
      <pre>{{ formattedPoints }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// Props with default values
const props = defineProps({
  hexId: {
    type: String,
    default: '822837fffffffff' // Default to San Francisco at resolution 2
  },
  width: {
    type: Number,
    default: 600
  },
  height: {
    type: Number,
    default: 600
  },
  fillColor: {
    type: String,
    default: '#ffffff'
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
  },
  showCoordinates: {
    type: Boolean,
    default: true
  }
})

// Center of the SVG
const center = ref({ x: props.width / 2, y: props.height / 2 })

// Size of the hexagon (radius from center to vertex)
const hexSize = ref(Math.min(props.width, props.height) * 0.4)

// Calculate hexagon points
const hexPoints = computed(() => {
  const points = []
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i
    const x = center.value.x + hexSize.value * Math.cos(angle)
    const y = center.value.y + hexSize.value * Math.sin(angle)
    points.push(`${x},${y}`)
  }
  return points.join(' ')
})

// Format points for debug display
const formattedPoints = computed(() => {
  return hexPoints.value.split(' ').join('\n')
})

// Computed style for the hexagon
const hexagonStyle = computed(() => {
  return {
    fill: props.fillColor,
    stroke: props.strokeColor,
    strokeWidth: `${props.strokeWidth}px`
  }
})

onMounted(() => {
  console.log('Simple Hexagon mounted with ID:', props.hexId)
  console.log('Hexagon points:', hexPoints.value)
})

// Expose methods and properties
defineExpose({
  hexPoints,
  center,
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

.hexagon-svg {
  max-width: 100%;
  max-height: 100%;
}

.coordinate-text {
  font-family: monospace;
  font-size: 14px;
  fill: #333;
  user-select: none;
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

pre {
  white-space: pre-wrap;
  font-size: 12px;
  max-height: 100px;
  overflow-y: auto;
  background-color: #f0f0f0;
  padding: 5px;
  border-radius: 3px;
}
</style>
