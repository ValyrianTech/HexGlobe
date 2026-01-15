/**
 * app.js - Main application for HexGlobe 3D
 * 
 * Initializes the 3D globe and handles user interactions
 */

class HexGlobeApp {
    constructor() {
        this.globe = null;
        this.currentResolution = 0;
        this.showAllHexagons = true;
        this.loadedTiles = {};  // Cache of loaded tiles by resolution
        
        this.init();
    }
    
    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing HexGlobe 3D...');
        
        // Create the 3D globe
        this.globe = new HexGlobe3D('globe-canvas');
        
        // Set up callbacks
        this.globe.onTileClick = (tileData) => this.handleTileClick(tileData);
        this.globe.onTileHover = (tileData) => this.handleTileHover(tileData);
        
        // Set up UI controls
        this.setupControls();
        
        // Load initial hexagon layer (resolution 0)
        await this.loadHexagonLayer(0);
        
        // Hide loading overlay
        this.hideLoading();
        
        console.log('HexGlobe 3D initialized successfully');
    }
    
    /**
     * Set up UI controls
     */
    setupControls() {
        // Resolution selector
        const resolutionSelect = document.getElementById('resolution-select');
        if (resolutionSelect) {
            resolutionSelect.addEventListener('change', async (e) => {
                const newResolution = parseInt(e.target.value);
                await this.changeResolution(newResolution);
            });
        }
        
        // Show all hexagons checkbox
        const showAllCheckbox = document.getElementById('show-all-hexagons');
        if (showAllCheckbox) {
            showAllCheckbox.addEventListener('change', async (e) => {
                this.showAllHexagons = e.target.checked;
                await this.refreshCurrentLayer();
            });
        }
    }
    
    /**
     * Load hexagons for a specific resolution
     * @param {number} resolution - H3 resolution level
     */
    async loadHexagonLayer(resolution) {
        console.log(`Loading hexagon layer for resolution ${resolution}...`);
        
        // Show loading state
        this.showLoading();
        
        try {
            // Check cache first
            if (this.loadedTiles[resolution]) {
                console.log(`Using cached tiles for resolution ${resolution}`);
                this.globe.addHexagonLayer(resolution, this.loadedTiles[resolution], this.showAllHexagons);
                this.hideLoading();
                return;
            }
            
            // Fetch tiles from API
            let tiles = [];
            
            if (resolution === 0) {
                // For resolution 0, get all base cells
                tiles = await hexGlobeAPI.getAllBaseCells();
            } else {
                // For other resolutions, get a grid centered on a default tile
                const defaultTile = hexGlobeAPI.getDefaultTileForResolution(resolution);
                const gridData = await hexGlobeAPI.getTileGrid(defaultTile, 10, 10);
                
                if (gridData && gridData.grid) {
                    const tileIds = [...new Set(Object.values(gridData.grid))];
                    
                    // Fetch full data for each tile
                    for (const tileId of tileIds) {
                        const tile = await hexGlobeAPI.getTile(tileId);
                        if (tile) {
                            tiles.push(tile);
                        }
                    }
                }
            }
            
            console.log(`Loaded ${tiles.length} tiles for resolution ${resolution}`);
            
            // Cache the tiles
            this.loadedTiles[resolution] = tiles;
            
            // Add to globe
            this.globe.addHexagonLayer(resolution, tiles, this.showAllHexagons);
            
        } catch (error) {
            console.error(`Error loading hexagon layer for resolution ${resolution}:`, error);
        }
        
        this.hideLoading();
    }
    
    /**
     * Change the current resolution
     * @param {number} newResolution - New resolution level
     */
    async changeResolution(newResolution) {
        if (newResolution === this.currentResolution) {
            return;
        }
        
        console.log(`Changing resolution from ${this.currentResolution} to ${newResolution}`);
        
        // Hide current layer
        this.globe.setLayerVisibility(this.currentResolution, false);
        
        // Load and show new layer
        this.currentResolution = newResolution;
        await this.loadHexagonLayer(newResolution);
        this.globe.setLayerVisibility(newResolution, true);
    }
    
    /**
     * Refresh the current layer (e.g., after changing visibility settings)
     */
    async refreshCurrentLayer() {
        await this.loadHexagonLayer(this.currentResolution);
    }
    
    /**
     * Handle tile click
     * @param {Object} tileData - The clicked tile's data
     */
    handleTileClick(tileData) {
        if (!tileData) return;
        
        console.log('Tile clicked:', tileData.id);
        
        // Update info panel
        this.updateInfoPanel(tileData, true);
    }
    
    /**
     * Handle tile hover
     * @param {Object} tileData - The hovered tile's data (or null)
     */
    handleTileHover(tileData) {
        // Could update a tooltip here
        // For now, we'll just update cursor style (handled in globe.js)
    }
    
    /**
     * Update the info panel with tile data
     * @param {Object} tileData - Tile data to display
     * @param {boolean} showNavButton - Whether to show navigation button
     */
    updateInfoPanel(tileData, showNavButton = false) {
        const infoPanel = document.getElementById('tile-info');
        if (!infoPanel) return;
        
        if (!tileData) {
            infoPanel.innerHTML = '<p>Click on a hexagon to view details</p>';
            return;
        }
        
        let html = `
            <p><strong>Tile ID:</strong></p>
            <p class="tile-id">${tileData.id}</p>
            <p><strong>Resolution:</strong> ${tileData.resolution || 'N/A'}</p>
        `;
        
        if (tileData.content) {
            html += `
                <p><strong>Content:</strong></p>
                <div class="tile-content">${tileData.content}</div>
            `;
        }
        
        if (showNavButton) {
            html += `
                <button class="nav-button" onclick="hexGlobeApp.navigateToTile('${tileData.id}')">
                    Navigate to Tile
                </button>
            `;
        }
        
        infoPanel.innerHTML = html;
    }
    
    /**
     * Navigate to a specific tile (opens in 2D UI for detailed view)
     * @param {string} tileId - The tile ID to navigate to
     */
    navigateToTile(tileId) {
        // Navigate to the 2D frontend with this tile
        const url = new URL('../frontend/index.html', window.location.href);
        url.searchParams.set('h3', tileId);
        url.searchParams.set('zoom', '3');
        
        window.location.href = url.toString();
    }
    
    /**
     * Show loading overlay
     */
    showLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.remove('hidden');
        }
    }
    
    /**
     * Hide loading overlay
     */
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }
}

// Initialize the application when DOM is ready
let hexGlobeApp;

document.addEventListener('DOMContentLoaded', () => {
    hexGlobeApp = new HexGlobeApp();
});
