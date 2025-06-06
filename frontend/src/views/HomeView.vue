<template>
  <div class="home">
    <div class="hex-container">
      <HexTile 
        :hexId="currentHexId" 
        :width="hexWidth" 
        :height="hexHeight" 
        :content="tileContent" 
        :fillColor="fillColor"
        :strokeColor="strokeColor"
        @navigate="navigateToTile"
      />
    </div>
    <div class="controls">
      <button @click="resetToDefaultTile">Reset to Default Tile</button>
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

// Navigate to a new tile
const navigateToTile = (hexId) => {
  console.log('Navigating to tile:', hexId);
  currentHexId.value = hexId;
  
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

.color-controls {
  margin-top: 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.color-controls label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

button {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  width: 100%;
  transition: background-color 0.3s;
}

button:hover {
  background-color: #45a049;
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
}

.navigation-history h3 {
  margin-top: 0;
  margin-bottom: 0;
  font-size: 16px;
  float: left;
  padding: 5px 15px 0 10px;
}

.navigation-history ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: nowrap;
  overflow-x: auto;
  height: 35px;
  align-items: center;
}

.navigation-history li {
  padding: 0 10px;
  cursor: pointer;
  white-space: nowrap;
  font-size: 14px;
  height: 35px;
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
