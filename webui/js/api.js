/**
 * api.js - API communication for HexGlobe 3D
 * 
 * Handles all communication with the HexGlobe backend API
 */

class HexGlobeAPI {
    constructor(baseUrl, modName = 'default') {
        this.baseUrl = baseUrl;
        this.modName = modName;
    }
    
    /**
     * Build URL with mod_name parameter
     */
    buildUrl(endpoint, params = {}) {
        const url = new URL(`${this.baseUrl}${endpoint}`);
        url.searchParams.set('mod_name', this.modName);
        
        for (const [key, value] of Object.entries(params)) {
            url.searchParams.set(key, value);
        }
        
        return url.toString();
    }
    
    /**
     * Get tile information
     */
    async getTile(tileId) {
        try {
            const url = this.buildUrl(`/tiles/${tileId}`);
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Failed to get tile: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error fetching tile ${tileId}:`, error);
            return null;
        }
    }
    
    /**
     * Get all tiles at a specific resolution that have content
     * This is a helper that fetches tiles and filters by content
     */
    async getTilesWithContent(resolution) {
        try {
            // For now, we'll use the grid endpoint centered on a default tile
            // In the future, this could be a dedicated endpoint
            const defaultTileId = this.getDefaultTileForResolution(resolution);
            const gridData = await this.getTileGrid(defaultTileId, 20, 20);
            
            if (!gridData || !gridData.grid) {
                return [];
            }
            
            // Fetch details for each tile and filter by content
            const tileIds = Object.values(gridData.grid);
            const tilesWithContent = [];
            
            for (const tileId of tileIds) {
                const tile = await this.getTile(tileId);
                if (tile && tile.content) {
                    tilesWithContent.push(tile);
                }
            }
            
            return tilesWithContent;
        } catch (error) {
            console.error(`Error fetching tiles with content:`, error);
            return [];
        }
    }
    
    /**
     * Get tile grid centered on a tile
     */
    async getTileGrid(tileId, width = 5, height = 5) {
        try {
            const url = this.buildUrl(`/tiles/${tileId}/grid`, { width, height });
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Failed to get grid: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error fetching grid for ${tileId}:`, error);
            return null;
        }
    }
    
    /**
     * Get neighbors of a tile
     */
    async getNeighbors(tileId) {
        try {
            const url = this.buildUrl(`/tiles/${tileId}/neighbors`);
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Failed to get neighbors: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error fetching neighbors for ${tileId}:`, error);
            return null;
        }
    }
    
    /**
     * Get all resolution IDs for a tile
     */
    async getResolutions(tileId) {
        try {
            const url = this.buildUrl(`/tiles/${tileId}/resolutions`);
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Failed to get resolutions: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error fetching resolutions for ${tileId}:`, error);
            return null;
        }
    }
    
    /**
     * Get all H3 base cells (resolution 0)
     * Resolution 0 has 122 cells (110 hexagons + 12 pentagons)
     */
    async getAllBaseCells() {
        try {
            // Use a known resolution 0 tile and get a large grid
            const baseTileId = '801ffffffffffff';
            const url = this.buildUrl(`/tiles/${baseTileId}/grid`, { width: 15, height: 15 });
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Failed to get base cells: ${response.statusText}`);
            }
            
            const gridData = await response.json();
            
            // Extract unique tile IDs
            const tileIds = new Set(Object.values(gridData.grid));
            
            // Fetch full tile data for each
            const tiles = [];
            for (const tileId of tileIds) {
                const tile = await this.getTile(tileId);
                if (tile) {
                    tiles.push(tile);
                }
            }
            
            return tiles;
        } catch (error) {
            console.error('Error fetching base cells:', error);
            return [];
        }
    }
    
    /**
     * Get default tile ID for a resolution
     */
    getDefaultTileForResolution(resolution) {
        const defaults = {
            0: '801ffffffffffff',
            1: '811fbffffffffff',
            2: '821fa7fffffffff',
            3: '831fa4fffffffff',
            4: '841fa45ffffffff',
            5: '851fa443fffffff'
        };
        
        return defaults[resolution] || defaults[0];
    }
}

// Create global API instance
const hexGlobeAPI = new HexGlobeAPI(CONFIG.api.baseUrl, CONFIG.api.modName);
