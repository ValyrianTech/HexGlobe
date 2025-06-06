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
            const response = await fetch(`${this.apiBaseUrl}/tiles/${this.activeTileId}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load tile: ${response.statusText}`);
            }
            
            const tileData = await response.json();
            this.activeTile = tileData;
            
            // Dispatch an event to notify that the active tile has changed
            const event = new CustomEvent('activeTileChanged', { detail: tileData });
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
            const event = new CustomEvent('activeTileChanged', { detail: fallbackTile });
            window.dispatchEvent(event);
            
            return fallbackTile;
        }
    }

    /**
     * Load the neighbors of the active tile from the API
     * @returns {Promise} - Promise that resolves when the neighbors are loaded
     */
    async loadNeighbors() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/tiles/${this.activeTileId}/neighbors`);
            
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
            // Use h3-js to calculate neighbors if available
            let fallbackNeighbors = [];
            
            if (window.h3) {
                try {
                    const neighborIndices = window.h3.kRing(this.activeTileId, 1).filter(
                        index => index !== this.activeTileId
                    );
                    
                    fallbackNeighbors = neighborIndices.map(id => ({
                        id: id,
                        content: `Fallback neighbor ${id}`,
                        visual_properties: {
                            border_color: "#0000FF",
                            border_thickness: 1,
                            border_style: "solid",
                            fill_color: "#F0F0F0"
                        }
                    }));
                } catch (h3Error) {
                    console.error("Error calculating neighbors with h3-js:", h3Error);
                    // Create 6 dummy neighbors if h3-js fails
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
                }
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
        
        // Load the new active tile and its neighbors
        await this.loadActiveTile();
        
        if (this.showNeighbors) {
            await this.loadNeighbors();
        }
        
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
            const response = await fetch(`${this.apiBaseUrl}/tiles/${this.activeTileId}/grid?width=${width}&height=${height}`);
            
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
                width: width,
                height: height,
                grid: Array(height).fill().map(() => Array(width).fill(this.activeTileId)),
                pentagon_positions: []
            };
            
            // Dispatch an event with the fallback grid
            const event = new CustomEvent('gridDataLoaded', { detail: fallbackGrid });
            window.dispatchEvent(event);
            
            return fallbackGrid;
        }
    }
}
