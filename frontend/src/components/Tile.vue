<template>
  <div 
    class="tile" 
    :class="{ active: isActive }"
    :style="tileStyles"
    @click="$emit('click')"
  >
    <div class="tile-content">{{ content || 'Empty' }}</div>
    <div class="tile-id">{{ id }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  id: {
    type: String,
    required: true
  },
  content: {
    type: String,
    default: ''
  },
  isActive: {
    type: Boolean,
    default: false
  },
  visualProperties: {
    type: Object,
    default: () => ({
      borderColor: '#000000',
      borderThickness: 1,
      borderStyle: 'solid',
      fillColor: '#f0f0f0'
    })
  }
})

defineEmits(['click'])

const tileStyles = computed(() => {
  const { borderColor, borderThickness, borderStyle, fillColor } = props.visualProperties
  
  return {
    backgroundColor: fillColor,
    border: `${borderThickness}px ${borderStyle} ${borderColor}`
  }
})
</script>

<style scoped>
.tile {
  position: relative;
  width: 100px;
  height: 115px;
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  user-select: none;
}

.tile:hover {
  transform: scale(1.05);
  z-index: 10;
}

.tile.active {
  transform: scale(1.1);
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
  z-index: 20;
}

.tile-content {
  font-size: 0.8rem;
  text-align: center;
  padding: 0 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 90%;
}

.tile-id {
  font-size: 0.6rem;
  position: absolute;
  bottom: 10px;
  opacity: 0.7;
}
</style>
