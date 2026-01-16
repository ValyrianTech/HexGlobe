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
        this.globe.onSelectionChange = (selectedIds) => this.handleSelectionChange(selectedIds);
        
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
        
        // Generate maps button
        const generateMapsBtn = document.getElementById('generate-maps-btn');
        if (generateMapsBtn) {
            generateMapsBtn.addEventListener('click', () => this.generateMapsForSelection());
        }
        
        // Clear selection button
        const clearSelectionBtn = document.getElementById('clear-selection-btn');
        if (clearSelectionBtn) {
            clearSelectionBtn.addEventListener('click', () => {
                this.globe.clearSelection();
                this.handleSelectionChange([]);
            });
        }
    }
    
    /**
     * Load hexagons for a specific resolution
     * @param {number} resolution - H3 resolution level
     * @param {boolean} noCache - If true, bypass browser cache when fetching tiles
     */
    async loadHexagonLayer(resolution, noCache = false) {
        console.log(`Loading hexagon layer for resolution ${resolution}...`);
        
        // Show loading state
        this.showLoading();
        
        try {
            // Check cache first (unless noCache is set)
            if (!noCache && this.loadedTiles[resolution]) {
                console.log(`Using cached tiles for resolution ${resolution}`);
                this.globe.addHexagonLayer(resolution, this.loadedTiles[resolution], this.showAllHexagons);
                this.hideLoading();
                return;
            }
            
            // Fetch tiles from API
            let tiles = [];
            
            if (resolution === 0) {
                // For resolution 0, get all base cells
                tiles = await hexGlobeAPI.getAllBaseCells(noCache);
            } else {
                // For other resolutions, get a grid centered on a default tile
                const defaultTile = hexGlobeAPI.getDefaultTileForResolution(resolution);
                const gridData = await hexGlobeAPI.getTileGrid(defaultTile, 10, 10);
                
                if (gridData && gridData.grid) {
                    const tileIds = [...new Set(Object.values(gridData.grid))];
                    
                    // Fetch full data for each tile
                    for (const tileId of tileIds) {
                        const tile = await hexGlobeAPI.getTile(tileId, noCache);
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
     * Handle selection change
     * @param {Array<string>} selectedIds - Array of selected tile IDs
     */
    handleSelectionChange(selectedIds) {
        const selectionInfo = document.getElementById('selection-info');
        const selectionCount = document.getElementById('selection-count');
        const generationStatus = document.getElementById('generation-status');
        
        if (selectionInfo && selectionCount) {
            if (selectedIds.length > 0) {
                selectionInfo.style.display = 'block';
                selectionCount.textContent = selectedIds.length;
            } else {
                selectionInfo.style.display = 'none';
            }
        }
        
        // Hide generation status when selection changes
        if (generationStatus) {
            generationStatus.style.display = 'none';
        }
    }
    
    /**
     * Generate maps for all selected tiles
     */
    async generateMapsForSelection() {
        const selectedIds = this.globe.getSelectedTileIds();
        if (selectedIds.length === 0) {
            return;
        }
        
        const generateBtn = document.getElementById('generate-maps-btn');
        const generationStatus = document.getElementById('generation-status');
        
        // Disable button during generation
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
        }
        
        // Show progress
        if (generationStatus) {
            generationStatus.style.display = 'block';
            generationStatus.className = 'progress';
            generationStatus.textContent = `Generating maps: 0/${selectedIds.length}`;
        }
        
        try {
            const results = await hexGlobeAPI.generateMapsForTiles(selectedIds, (current, total) => {
                if (generationStatus) {
                    generationStatus.textContent = `Generating maps: ${current}/${total}`;
                }
            });
            
            // Count successes and failures
            const successes = results.filter(r => r.success).length;
            const failures = results.filter(r => !r.success).length;
            
            if (generationStatus) {
                if (failures === 0) {
                    generationStatus.className = 'success';
                    generationStatus.textContent = `Successfully generated ${successes} maps!`;
                } else {
                    generationStatus.className = 'error';
                    generationStatus.textContent = `Generated ${successes} maps, ${failures} failed`;
                }
            }
            
            // Refresh the current layer to show new textures
            // Clear tile cache and force fresh fetch from API
            delete this.loadedTiles[this.currentResolution];
            await this.loadHexagonLayer(this.currentResolution, true);  // noCache = true
            
            // Update selection UI since layer rebuild clears selection
            this.handleSelectionChange([]);
            
        } catch (error) {
            console.error('Error generating maps:', error);
            if (generationStatus) {
                generationStatus.className = 'error';
                generationStatus.textContent = `Error: ${error.message}`;
            }
        }
        
        // Re-enable button
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Maps';
        }
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
