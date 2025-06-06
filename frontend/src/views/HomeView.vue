<template>
  <div class="home">
    <div class="hex-container">
      <HexTile 
        ref="hexTileRef"
        :hexId="currentHexId" 
        :width="hexWidth" 
        :height="hexHeight" 
        :content="tileContent" 
        :fillColor="fillColor"
        :strokeColor="strokeColor"
        @navigate="navigateToTile"
        @selectNeighbor="handleNeighborSelection"
      />
    </div>
    <div class="controls">
      <div class="tile-info-panel">
        <h3>Tile Information</h3>
        <p><strong>Tile ID:</strong> {{ currentHexId.substring(0, 8) }}...</p>
        <p><strong>Resolution:</strong> {{ tileResolution }}</p>
        <p><strong>Content:</strong> {{ tileContent || 'None' }}</p>
        
        <div class="visual-props">
          <p><strong>Visual Properties:</strong></p>
          <div class="color-controls">
            <label>
              Fill Color:
              <input type="color" v-model="fillColor">
            </label>
            <label>
              Border Color:
              <input type="color" v-model="strokeColor">
            </label>
          </div>
        </div>
        
        <div class="action-buttons">
          <button @click="resetToDefaultTile">Reset to Default</button>
          <button @click="toggleNeighbors">{{ showNeighbors ? 'Hide' : 'Show' }} Neighbors</button>
        </div>
        
        <div v-if="selectedNeighborId" class="selected-info">
          <p><strong>Selected:</strong> {{ selectedNeighborId.substring(0, 6) }}...</p>
          <button @click="navigateToSelectedNeighbor" class="navigate-btn">Navigate to Selected</button>
        </div>
      </div>
    </div>
  </div>
  <div class="navigation-history">
    <h3>Navigation History</h3>
    <ul>
      <li v-for="(tile, index) in navigationHistory" :key="index" @click="navigateToHistoryTile(tile)">
        {{ tile.substring(0, 8) }}... <span v-if="tile === currentHexId">(current)</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue';
import HexTile from '@/components/HexTile.vue';

// Default hex ID (San Francisco at resolution 2)
const DEFAULT_HEX_ID = '822837fffffffff';

// Current hex ID and content
const currentHexId = ref(DEFAULT_HEX_ID);
const tileContent = ref('Welcome to HexGlobe!');
const fillColor = ref('#f0f0f0');
const strokeColor = ref('#ff0000');

// Navigation history
const navigationHistory = ref([DEFAULT_HEX_ID]);

// Responsive dimensions for the hexagon
const hexWidth = ref(window.innerWidth * 0.95);
const hexHeight = ref(window.innerHeight * 0.85);

// Reference to the HexTile component
const hexTileRef = ref(null);

// Computed properties for tile information
const tileResolution = computed(() => {
  return hexTileRef.value?.resolution || '?';
});

const showNeighbors = computed(() => {
  return hexTileRef.value?.showNeighbors || false;
});

// Selected neighbor
const selectedNeighborId = ref(null);

// Handle window resize
const handleResize = () => {
  hexWidth.value = window.innerWidth * 0.95;
  hexHeight.value = window.innerHeight * 0.85;
};

// Add resize event listener
onMounted(() => {
  window.addEventListener('resize', handleResize);
  console.log('HomeView mounted');
});

// Clean up event listener
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});

// Toggle neighbors
const toggleNeighbors = () => {
  if (hexTileRef.value) {
    hexTileRef.value.toggleNeighbors();
  }
};

// Handle neighbor selection
const handleNeighborSelection = (neighborId) => {
  selectedNeighborId.value = neighborId;
};

// Navigate to selected neighbor
const navigateToSelectedNeighbor = () => {
  if (hexTileRef.value && selectedNeighborId.value) {
    hexTileRef.value.navigateToNeighbor();
  }
};

// Navigate to a new tile
const navigateToTile = (hexId) => {
  console.log('Navigating to tile:', hexId);
  currentHexId.value = hexId;
  selectedNeighborId.value = null;
  
  // Add to navigation history if not already the last item
  if (navigationHistory.value[navigationHistory.value.length - 1] !== hexId) {
    navigationHistory.value.push(hexId);
    
    // Limit history length
    if (navigationHistory.value.length > 10) {
      navigationHistory.value.shift();
    }
  }
  
  // In a real application, we would fetch the tile content from the backend
  tileContent.value = `Tile ${hexId.substring(0, 8)}...`;
};

// Navigate to a tile from history
const navigateToHistoryTile = (hexId) => {
  if (hexId !== currentHexId.value) {
    navigateToTile(hexId);
  }
};

// Reset to default tile
const resetToDefaultTile = () => {
  navigateToTile(DEFAULT_HEX_ID);
};
</script>

<style scoped>
.home {
  display: grid;
  grid-template-columns: 1fr 160px;
  grid-template-rows: 1fr;
  grid-template-areas: "main sidebar";
  gap: 0;
  padding: 0;
  height: calc(100vh - 35px);
  margin: 0;
  overflow: visible;
}

.hex-container {
  grid-area: main;
  height: 100%;
  width: 100%;
  background-color: #f5f5f5;
  border-radius: 0;
  overflow: visible;
  box-shadow: none;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0;
  margin: 0;
}

.controls {
  grid-area: sidebar;
  padding: 10px;
  background-color: #fff;
  border-radius: 0;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  margin: 0;
  height: 100%;
  width: 160px;
  overflow-y: auto;
}

.tile-info-panel h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  color: #333;
}

.tile-info-panel p {
  margin: 5px 0;
  font-size: 12px;
  word-break: break-word;
}

.visual-props {
  margin-top: 10px;
}

.color-controls {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.color-controls label {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  margin-bottom: 5px;
}

.color-controls input {
  width: 100%;
  margin-top: 3px;
}

.action-buttons {
  margin-top: 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

button {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  width: 100%;
  transition: background-color 0.3s;
  white-space: nowrap;
}

button:hover {
  background-color: #45a049;
}

.selected-info {
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
}

.navigate-btn {
  background-color: #2196F3;
  margin-top: 5px;
}

.navigate-btn:hover {
  background-color: #0b7dda;
}

.navigation-history {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0;
  background-color: #f5f5f5;
  border-top: 1px solid #ddd;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 100;
  height: 35px;
  overflow: hidden;
  display: flex;
  align-items: center;
}

.navigation-history h3 {
  margin: 0;
  font-size: 14px;
  padding: 0 10px;
}

.navigation-history ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
  display: flex;
  overflow-x: auto;
  white-space: nowrap;
  flex-grow: 1;
}

.navigation-history li {
  display: inline-block;
  padding: 0 10px;
  cursor: pointer;
  font-size: 12px;
  border-right: 1px solid #ddd;
  line-height: 35px;
}

.navigation-history li:hover {
  background-color: #e0e0e0;
}

.navigation-history li span {
  font-weight: bold;
  color: #4CAF50;
}
</style>
