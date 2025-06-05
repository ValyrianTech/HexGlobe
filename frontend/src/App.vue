<template>
  <div class="app">
    <header>
      <h1>HexGlobe</h1>
    </header>
    <main>
      <router-view />
    </main>
    <ErrorDisplay />
  </div>
</template>

<script setup>
import ErrorDisplay from './components/ErrorDisplay.vue'
// App component setup
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: Arial, sans-serif;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
}

header {
  background-color: #333;
  color: white;
  padding: 0.5rem 1rem;
  text-align: center;
  z-index: 1000;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

header h1 {
  margin: 0;
  font-size: 1.5rem;
}

main {
  flex: 1;
  overflow: hidden;
  position: relative;
}
</style>
