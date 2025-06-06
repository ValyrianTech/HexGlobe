<template>
  <div class="home">
    <h1>HexGlobe</h1>
    <div class="hex-container">
      <HexTile 
        :hexId="currentHexId" 
        :width="800" 
        :height="600" 
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
    <div class="navigation-history">
      <h3>Navigation History</h3>
      <ul>
        <li v-for="(tile, index) in navigationHistory" :key="index" @click="navigateToHistoryTile(tile)">
          {{ tile.substring(0, 8) }}... <span v-if="tile === currentHexId">(current)</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
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

// Initialize
onMounted(() => {
  console.log('HomeView mounted');
});
</script>

<style scoped>
.home {
  display: grid;
  grid-template-columns: 1fr 250px;
  grid-template-rows: auto 1fr;
  grid-template-areas:
    "header header"
    "main sidebar";
  gap: 20px;
  padding: 20px;
  height: calc(100vh - 40px);
}

h1 {
  grid-area: header;
  margin: 0 0 20px 0;
  color: #333;
  text-align: center;
}

.hex-container {
  grid-area: main;
  height: 100%;
  background-color: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.controls {
  grid-area: sidebar;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.color-controls {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
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
  margin-top: 20px;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.navigation-history h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
}

.navigation-history ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.navigation-history li {
  padding: 8px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  font-family: monospace;
}

.navigation-history li:hover {
  background-color: #f5f5f5;
}

.navigation-history li:last-child {
  border-bottom: none;
}

.navigation-history li span {
  color: #4CAF50;
  font-weight: bold;
}
</style>
