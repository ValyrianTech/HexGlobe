<template>
  <div v-if="hasErrors" class="error-container">
    <div class="error-header">
      <h3>Debug Information</h3>
      <button @click="clearErrors">Clear</button>
    </div>
    <div class="error-content">
      <div v-for="(error, index) in errors" :key="index" class="error-item">
        <span class="error-time">{{ error.time }}</span>
        <span class="error-message">{{ error.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const errors = ref([])
const hasErrors = computed(() => errors.value.length > 0)

// Add error to the list
const addError = (message) => {
  const now = new Date()
  const timeString = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`
  errors.value.push({ time: timeString, message })
}

// Clear all errors
const clearErrors = () => {
  errors.value = []
}

// Override console.error to capture errors
const originalConsoleError = console.error
console.error = (...args) => {
  originalConsoleError(...args)
  addError(args.join(' '))
}

// Expose methods
defineExpose({
  addError,
  clearErrors
})
</script>

<style scoped>
.error-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 400px;
  max-height: 300px;
  background-color: rgba(255, 255, 255, 0.9);
  border: 1px solid #ff6b6b;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  z-index: 2000;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.error-header {
  background-color: #ff6b6b;
  color: white;
  padding: 8px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-header h3 {
  margin: 0;
  font-size: 16px;
}

.error-header button {
  background: transparent;
  border: 1px solid white;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  cursor: pointer;
}

.error-content {
  padding: 8px;
  overflow-y: auto;
  max-height: 250px;
}

.error-item {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
  font-size: 12px;
}

.error-time {
  color: #666;
  margin-right: 8px;
}

.error-message {
  color: #d32f2f;
}
</style>
