import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Import Leaflet CSS
import 'leaflet/dist/leaflet.css'

// Create Vue app
const app = createApp(App)

// Use plugins
app.use(createPinia())
app.use(router)

// Mount app
app.mount('#app')
