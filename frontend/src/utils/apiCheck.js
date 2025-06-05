import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

/**
 * Check if the backend API is accessible
 * @returns {Promise<boolean>} True if the API is accessible, false otherwise
 */
export const checkApiConnection = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`)
    return response.status === 200
  } catch (error) {
    console.error('API connection check failed:', error)
    return false
  }
}

/**
 * Get a specific tile by ID
 * @param {string} tileId The H3 index of the tile to fetch
 * @returns {Promise<object>} The tile data
 */
export const getTile = async (tileId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tiles/${tileId}`)
    return response.data
  } catch (error) {
    console.error(`Error fetching tile ${tileId}:`, error)
    throw error
  }
}

/**
 * Get the neighbors of a specific tile
 * @param {string} tileId The H3 index of the tile
 * @returns {Promise<Array>} Array of neighboring tile IDs
 */
export const getNeighbors = async (tileId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tiles/${tileId}/neighbors`)
    return response.data.neighbors
  } catch (error) {
    console.error(`Error fetching neighbors for tile ${tileId}:`, error)
    throw error
  }
}

/**
 * Get a list of available tiles from the backend
 * @returns {Promise<Array>} Array of available tile IDs
 */
export const getAvailableTiles = async () => {
  try {
    // This is a placeholder - the actual endpoint would depend on your backend implementation
    const response = await axios.get(`${API_BASE_URL}/tiles`)
    return response.data
  } catch (error) {
    console.error('Error fetching available tiles:', error)
    throw error
  }
}

export default {
  checkApiConnection,
  getTile,
  getNeighbors,
  getAvailableTiles
}
