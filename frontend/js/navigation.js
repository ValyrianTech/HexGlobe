/**
 * navigation.js - Module for handling tile navigation
 * 
 * This module provides functionality for navigating between tiles,
 * managing neighbors, and handling user interactions.
 */

class HexNavigation {
    /**
     * Create a new HexNavigation instance
     * @param {Object} options - Configuration options
     */
    constructor(options = {}) {
        this.activeTileId = options.initialTileId || "8828308280fffff"; // Default to a valid H3 index
        this.neighbors = [];
        this.showNeighbors = true;
        this.apiBaseUrl = options.apiBaseUrl || "http://localhost:8000/api";
        this.isGeneratingMap = false; // Track if map generation is in progress
    }

    /**
     * Initialize the navigation system
     * @returns {Promise} - Promise that resolves when initialization is complete
     */
    async initialize() {
        try {
            // Load the active tile
            await this.loadActiveTile();
            
            // Load the neighbors
            if (this.showNeighbors) {
                await this.loadNeighbors();
            }
            
            return true;
        } catch (error) {
            console.error("Failed to initialize navigation:", error);
            return false;
        }
    }

    /**
     * Load the active tile from the API
     * @returns {Promise} - Promise that resolves when the tile is loaded
     */
    async loadActiveTile() {
        try {
            const modName = window.modLoader ? window.modLoader.getModName() : 'default';
            const response = await fetch(`${this.apiBaseUrl}/tiles/${this.activeTileId}?mod_name=${modName}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load tile: ${response.statusText}`);
            }
            
            const tileData = await response.json();
            this.activeTile = tileData;
            
            // Check if the active tile has a map image
            // If not, trigger map generation
            if (!tileData.latest_map && !this.isGeneratingMap) {
                console.log(`No map found for active tile ${tileData.id}, triggering map generation...`);
                this.generateMapForActiveTile(tileData.id);
            }
            
            // Dispatch an event to notify that the active tile has changed
            // Include the resolution from the backend in the event
            const event = new CustomEvent('activeTileChanged', { 
                detail: {
                    ...tileData,
                    // Ensure resolution is available in the event
                    resolution: tileData.resolution !== undefined ? tileData.resolution : null
                }
            });
            window.dispatchEvent(event);
            
            return tileData;
        } catch (error) {
            console.error("Error loading active tile:", error);
            
            // If the API fails, create a fallback tile for development purposes
            const fallbackTile = {
                id: this.activeTileId,
                content: "Fallback content for development",
                visual_properties: {
                    border_color: "#FF0000",
                    border_thickness: 2,
                    border_style: "solid",
                    fill_color: "#FFFFFF"
                }
            };
            
            this.activeTile = fallbackTile;
            
            // Dispatch an event with the fallback tile
            const event = new CustomEvent('activeTileChanged', { 
                detail: {
                    ...fallbackTile,
                    // Ensure resolution is available in the event
                    resolution: fallbackTile.resolution !== undefined ? fallbackTile.resolution : null
                }
            });
            window.dispatchEvent(event);
            
            return fallbackTile;
        }
    }

    /**
     * Generate a map for the active tile
     * @param {string} tileId - The ID of the tile to generate a map for
     * @returns {Promise} - Promise that resolves when map generation is complete
     */
    async generateMapForActiveTile(tileId) {
        // Set flag to prevent multiple simultaneous generation attempts
        this.isGeneratingMap = true;
        
        // Create and show status message
        const statusElement = document.createElement('div');
        statusElement.id = 'map-generation-status';
        statusElement.style.position = 'fixed';
        statusElement.style.bottom = '20px';
        statusElement.style.right = '20px';
        statusElement.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        statusElement.style.color = 'white';
        statusElement.style.padding = '10px';
        statusElement.style.borderRadius = '5px';
        statusElement.style.zIndex = '1000';
        statusElement.textContent = `Generating map for active tile ${tileId}...`;
        document.body.appendChild(statusElement);
        
        try {
            console.log(`Calling API to generate map for tile ${tileId}...`);
            
            // Call the API to generate the map
            const response = await fetch(`${this.apiBaseUrl}/tiles/${tileId}/generate-map`, {
                method: 'POST',
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            
            const data = await response.json();
            console.log(`Map generated successfully for tile ${tileId}:`, data);
            
            // Update status message
            statusElement.textContent = `Map generated successfully! Refreshing...`;
            statusElement.style.backgroundColor = 'rgba(0, 128, 0, 0.7)';
            
            // Wait a moment to show the success message before refreshing
            setTimeout(() => {
                // Reload the page to show the new map
                window.location.reload();
            }, 1500);
            
        } catch (error) {
            console.error(`Error generating map for tile ${tileId}:`, error);
            
            // Update status message with error
            statusElement.textContent = `Error generating map: ${error.message}`;
            statusElement.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
            
            // Remove the status message after a delay
            setTimeout(() => {
                if (document.body.contains(statusElement)) {
                    document.body.removeChild(statusElement);
                }
            }, 5000);
            
        } finally {
            // Reset the flag
            this.isGeneratingMap = false;
        }
    }

    /**
     * Load the neighbors of the active tile from the API
     * @returns {Promise} - Promise that resolves when the neighbors are loaded
     */
    async loadNeighbors() {
        try {
            const modName = window.modLoader ? window.modLoader.getModName() : 'default';
            const response = await fetch(`${this.apiBaseUrl}/tiles/${this.activeTileId}/neighbors?mod_name=${modName}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load neighbors: ${response.statusText}`);
            }
            
            const neighborsData = await response.json();
            this.neighbors = neighborsData;
            
            // Dispatch an event to notify that the neighbors have changed
            const event = new CustomEvent('neighborsChanged', { detail: neighborsData });
            window.dispatchEvent(event);
            
            return neighborsData;
        } catch (error) {
            console.error("Error loading neighbors:", error);
            
            // If the API fails, create fallback neighbors for development
            let fallbackNeighbors = [];
            
            // Create 6 dummy neighbors as fallback if API fails
            for (let i = 0; i < 6; i++) {
                fallbackNeighbors.push({
                    id: `dummy-neighbor-${i}`,
                    content: `Fallback neighbor ${i}`,
                    visual_properties: {
                        border_color: "#0000FF",
                        border_thickness: 1,
                        border_style: "solid",
                        fill_color: "#F0F0F0"
                    }
                });
            }
            
            this.neighbors = fallbackNeighbors;
            
            // Dispatch an event with the fallback neighbors
            const event = new CustomEvent('neighborsChanged', { detail: fallbackNeighbors });
            window.dispatchEvent(event);
            
            return fallbackNeighbors;
        }
    }

    /**
     * Navigate to a new tile
     * @param {string} tileId - The ID of the tile to navigate to
     * @returns {Promise} - Promise that resolves when navigation is complete
     */
    async navigateTo(tileId) {
        // Store the previous tile ID for animation purposes
        const previousTileId = this.activeTileId;
        
        // Update the active tile ID
        this.activeTileId = tileId;
        
        // Dispatch an event to notify that navigation has started
        const startEvent = new CustomEvent('navigationStarted', { 
            detail: { 
                previousTileId, 
                newTileId: tileId 
            } 
        });
        window.dispatchEvent(startEvent);
        
        // Load the new active tile
        await this.loadActiveTile();
        
        // Dispatch an event to notify that navigation has completed
        const completeEvent = new CustomEvent('navigationCompleted', { 
            detail: { 
                previousTileId, 
                newTileId: tileId,
                activeTile: this.activeTile,
                neighbors: this.neighbors
            } 
        });
        window.dispatchEvent(completeEvent);
        
        return true;
    }

    /**
     * Toggle the visibility of neighbors
     * @param {boolean} show - Whether to show neighbors
     * @returns {Promise} - Promise that resolves when the operation is complete
     */
    async toggleNeighbors(show) {
        this.showNeighbors = show !== undefined ? show : !this.showNeighbors;
        
        if (this.showNeighbors) {
            await this.loadNeighbors();
        } else {
            this.neighbors = [];
            
            // Dispatch an event to notify that the neighbors have changed
            const event = new CustomEvent('neighborsChanged', { detail: [] });
            window.dispatchEvent(event);
        }
        
        return this.showNeighbors;
    }

    /**
     * Get the active tile
     * @returns {Object} - The active tile
     */
    getActiveTile() {
        return this.activeTile;
    }

    /**
     * Get the neighbors of the active tile
     * @returns {Array} - The neighbors
     */
    getNeighbors() {
        return this.neighbors;
    }

    /**
     * Fetch a grid of tiles centered around the active tile
     * @param {number} width - Width of the grid (number of columns)
     * @param {number} height - Height of the grid (number of rows)
     * @returns {Promise} - Promise that resolves with the grid data
     */
    async fetchTileGrid(width, height) {
        try {
            const modName = window.modLoader ? window.modLoader.getModName() : 'default';
            const response = await fetch(`${this.apiBaseUrl}/tiles/${this.activeTileId}/grid?width=${width}&height=${height}&mod_name=${modName}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load grid: ${response.statusText}`);
            }
            
            const gridData = await response.json();
            
            // Dispatch an event to notify that the grid data has been loaded
            const event = new CustomEvent('gridDataLoaded', { detail: gridData });
            window.dispatchEvent(event);
            
            return gridData;
        } catch (error) {
            console.error("Error loading grid data:", error);
            
            // If the API fails, create a fallback grid for development
            const fallbackGrid = {
                center_tile_id: this.activeTileId,
                grid: {},
                pentagon_positions: [],
                bounds: {
                    min_row: -Math.floor(height/2),
                    max_row: Math.floor(height/2),
                    min_col: -Math.floor(width/2),
                    max_col: Math.floor(width/2)
                }
            };
            
            // Create a grid with coordinates as keys
            for (let row = fallbackGrid.bounds.min_row; row <= fallbackGrid.bounds.max_row; row++) {
                for (let col = fallbackGrid.bounds.min_col; col <= fallbackGrid.bounds.max_col; col++) {
                    fallbackGrid.grid[`${col},${row}`] = this.activeTileId;
                }
            }
            
            // Dispatch an event with the fallback grid
            const event = new CustomEvent('gridDataLoaded', { detail: fallbackGrid });
            window.dispatchEvent(event);
            
            return fallbackGrid;
        }
    }

    /**
     * Update the content of the active tile
     * @param {string} content - The new content for the tile
     * @returns {Promise} - Promise that resolves when the update is complete
     */
    async updateTileContent(content) {
        try {
            const modName = window.modLoader ? window.modLoader.getModName() : 'default';
            const response = await fetch(`${this.apiBaseUrl}/tiles/${this.activeTileId}?mod_name=${modName}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to update tile content: ${response.statusText}`);
            }
            
            const updatedTileData = await response.json();
            this.activeTile = updatedTileData.tile;
            
            // Dispatch an event to notify that the tile content has been updated
            const event = new CustomEvent('tileContentUpdated', { 
                detail: updatedTileData.tile
            });
            window.dispatchEvent(event);
            
            return updatedTileData.tile;
        } catch (error) {
            console.error("Error updating tile content:", error);
            throw error;
        }
    }

    /**
     * Move content from the active tile to another tile
     * @param {string} targetTileId - The ID of the target tile to move content to
     * @returns {Promise} - Promise that resolves when the move is complete
     */
    async moveContent(targetTileId) {
        try {
            const modName = window.modLoader ? window.modLoader.getModName() : 'default';
            const response = await fetch(`${this.apiBaseUrl}/tiles/${this.activeTileId}/move-content/${targetTileId}?mod_name=${modName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to move tile content: ${response.statusText}`);
            }
            
            const responseData = await response.json();
            
            // Reload the active tile to reflect the content change
            await this.loadActiveTile();
            
            // Dispatch an event to notify that the tile content has been moved
            const event = new CustomEvent('tileContentMoved', { 
                detail: {
                    sourceTileId: this.activeTileId,
                    targetTileId: targetTileId,
                    result: responseData
                }
            });
            window.dispatchEvent(event);
            
            return responseData;
        } catch (error) {
            console.error("Error moving tile content:", error);
            throw error;
        }
    }
}
