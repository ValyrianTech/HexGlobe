<template>
  <div class="home">
    <HexTile />
  </div>
</template>

<script setup>
import HexTile from '../components/HexTile.vue'
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.home {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
