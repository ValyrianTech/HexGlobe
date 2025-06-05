import { defineStore } from 'pinia'
import axios from 'axios'

// Base API URL
const API_BASE_URL = 'http://localhost:8000/api'

export const useTileStore = defineStore('tile', {
  state: () => ({
    activeTile: null,
    neighbors: [],
    loading: false,
    error: null
  }),
  
  getters: {
    hasActiveTile: (state) => !!state.activeTile,
    neighborCount: (state) => state.neighbors.length
  },
  
  actions: {
    async fetchTile(tileId) {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get(`${API_BASE_URL}/tiles/${tileId}`)
        this.activeTile = response.data
      } catch (error) {
        console.error('Error fetching tile:', error)
        this.error = 'Failed to load tile data'
      } finally {
        this.loading = false
      }
    },
    
    async fetchNeighbors(tileId) {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get(`${API_BASE_URL}/tiles/${tileId}/neighbors`)
        this.neighbors = response.data.neighbors
      } catch (error) {
        console.error('Error fetching neighbors:', error)
        this.error = 'Failed to load neighboring tiles'
      } finally {
        this.loading = false
      }
    },
    
    async updateTileContent(tileId, content) {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.patch(`${API_BASE_URL}/tiles/${tileId}/content`, { content })
        
        // Update active tile if it's the one being modified
        if (this.activeTile && this.activeTile.id === tileId) {
          this.activeTile = response.data
        }
        
        return response.data
      } catch (error) {
        console.error('Error updating tile content:', error)
        this.error = 'Failed to update tile content'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async updateVisualProperties(tileId, visualProperties) {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.patch(`${API_BASE_URL}/tiles/${tileId}/visual`, visualProperties)
        
        // Update active tile if it's the one being modified
        if (this.activeTile && this.activeTile.id === tileId) {
          this.activeTile = response.data
        }
        
        return response.data
      } catch (error) {
        console.error('Error updating visual properties:', error)
        this.error = 'Failed to update visual properties'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async moveContent(fromTileId, toTileId) {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.post(`${API_BASE_URL}/tiles/${fromTileId}/move-content/${toTileId}`)
        
        // Refresh both tiles data
        await this.fetchTile(this.activeTile?.id || fromTileId)
        await this.fetchNeighbors(this.activeTile?.id || fromTileId)
        
        return response.data
      } catch (error) {
        console.error('Error moving content:', error)
        this.error = 'Failed to move content between tiles'
        throw error
      } finally {
        this.loading = false
      }
    }
  }
})
