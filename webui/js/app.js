/**
 * app.js - Main application for HexGlobe 3D
 * 
 * Initializes the 3D globe and handles user interactions
 */

class HexGlobeApp {
    constructor() {
        this.globe = null;
        this.tileView = null;
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
        
        // Create the 2D tile view
        this.tileView = new TileView2D('tile-canvas', 'tile-view-placeholder');
        
        // Set up callbacks
        this.globe.onTileClick = (tileData) => this.handleTileClick(tileData);
        this.globe.onTileHover = (tileData) => this.handleTileHover(tileData);
        this.globe.onSelectionChange = (selectedIds) => this.handleSelectionChange(selectedIds);
        
        // Set up UI controls
        this.setupControls();
        
        // Load initial hexagon layer (resolution 0)
        await this.loadHexagonLayer(0);
        this.globe.setZoomSpeedForResolution(0);
        
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
        
        // Go To button
        const gotoBtn = document.getElementById('goto-btn');
        const gotoInput = document.getElementById('goto-input');
        if (gotoBtn && gotoInput) {
            gotoBtn.addEventListener('click', () => this.handleGoTo());
            gotoInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.handleGoTo();
            });
        }
        
        // Update content button
        const updateContentBtn = document.getElementById('update-content-btn');
        if (updateContentBtn) {
            updateContentBtn.addEventListener('click', () => this.handleUpdateContent());
        }
        
        // Move content button
        const moveContentBtn = document.getElementById('move-content-btn');
        if (moveContentBtn) {
            moveContentBtn.addEventListener('click', () => this.handleMoveContent());
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
        
        // Adjust zoom speed for the new resolution
        this.globe.setZoomSpeedForResolution(newResolution);
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
        
        // Update 2D tile view
        this.tileView.showTile(tileData);
        
        // Show content editor
        this.showContentEditor(tileData);
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
                // Clear 2D tile view when selection is cleared
                this.tileView.clear();
                // Hide content editor
                this.hideContentEditor();
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
     * Handle Go To navigation
     */
    async handleGoTo() {
        const input = document.getElementById('goto-input');
        const btn = document.getElementById('goto-btn');
        if (!input || !input.value.trim()) return;
        
        const value = input.value.trim();
        const isH3Index = /^[0-9a-fA-F]+$/.test(value);
        
        btn.disabled = true;
        btn.textContent = 'Loading...';
        
        try {
            let tileId;
            
            if (isH3Index) {
                tileId = value;
            } else {
                // Geocode the address
                const result = await hexGlobeAPI.geocode(value, this.currentResolution);
                if (result && result.h3_index) {
                    tileId = result.h3_index;
                } else {
                    throw new Error('Could not geocode address');
                }
            }
            
            // Fetch the tile data
            const tileData = await hexGlobeAPI.getTile(tileId);
            if (tileData) {
                // Update resolution if different
                if (tileData.resolution !== undefined && tileData.resolution !== this.currentResolution) {
                    const resolutionSelect = document.getElementById('resolution-select');
                    if (resolutionSelect) {
                        resolutionSelect.value = tileData.resolution;
                    }
                    await this.changeResolution(tileData.resolution);
                }
                
                // Focus on the tile position
                if (tileData.geometry && tileData.geometry.length > 0) {
                    let centerLat = 0, centerLng = 0;
                    tileData.geometry.forEach(([lat, lng]) => {
                        centerLat += lat;
                        centerLng += lng;
                    });
                    centerLat /= tileData.geometry.length;
                    centerLng /= tileData.geometry.length;
                    
                    this.globe.focusOnPosition(centerLat, centerLng);
                }
                
                // Update UI
                this.updateInfoPanel(tileData, true);
                this.tileView.showTile(tileData);
                this.showContentEditor(tileData);
                
                input.value = '';
            }
        } catch (error) {
            console.error('Error navigating to tile:', error);
            alert(`Error: ${error.message}`);
        }
        
        btn.disabled = false;
        btn.textContent = 'Go';
    }
    
    /**
     * Show content editor for a tile
     * @param {Object} tileData - The tile data
     */
    showContentEditor(tileData) {
        const contentEditor = document.getElementById('content-editor');
        const moveSection = document.getElementById('move-content-section');
        const tileContent = document.getElementById('tile-content');
        
        if (contentEditor && tileContent) {
            contentEditor.style.display = 'block';
            tileContent.value = tileData.content || '';
            contentEditor.dataset.tileId = tileData.id;
        }
        
        if (moveSection) {
            moveSection.style.display = 'block';
            moveSection.dataset.tileId = tileData.id;
        }
    }
    
    /**
     * Hide content editor
     */
    hideContentEditor() {
        const contentEditor = document.getElementById('content-editor');
        const moveSection = document.getElementById('move-content-section');
        
        if (contentEditor) {
            contentEditor.style.display = 'none';
        }
        if (moveSection) {
            moveSection.style.display = 'none';
        }
    }
    
    /**
     * Handle update content button click
     */
    async handleUpdateContent() {
        const contentEditor = document.getElementById('content-editor');
        const tileContent = document.getElementById('tile-content');
        const updateStatus = document.getElementById('update-status');
        const updateBtn = document.getElementById('update-content-btn');
        
        if (!contentEditor || !tileContent) return;
        
        const tileId = contentEditor.dataset.tileId;
        const content = tileContent.value;
        
        if (!tileId) return;
        
        updateBtn.disabled = true;
        updateStatus.textContent = 'Updating...';
        updateStatus.className = 'status-message loading';
        
        try {
            await hexGlobeAPI.updateTileContent(tileId, content);
            
            updateStatus.textContent = 'Content updated successfully!';
            updateStatus.className = 'status-message success';
            
            // Refresh tile data
            const tileData = await hexGlobeAPI.getTile(tileId, true);
            if (tileData) {
                this.updateInfoPanel(tileData, true);
            }
            
            setTimeout(() => {
                updateStatus.textContent = '';
                updateStatus.className = 'status-message';
            }, 3000);
        } catch (error) {
            updateStatus.textContent = `Error: ${error.message}`;
            updateStatus.className = 'status-message error';
            
            setTimeout(() => {
                updateStatus.textContent = '';
                updateStatus.className = 'status-message';
            }, 5000);
        }
        
        updateBtn.disabled = false;
    }
    
    /**
     * Handle move content button click
     */
    async handleMoveContent() {
        const moveSection = document.getElementById('move-content-section');
        const moveTarget = document.getElementById('move-target');
        const moveStatus = document.getElementById('move-status');
        const moveBtn = document.getElementById('move-content-btn');
        
        if (!moveSection || !moveTarget) return;
        
        const sourceTileId = moveSection.dataset.tileId;
        const targetTileId = moveTarget.value.trim();
        
        if (!sourceTileId || !targetTileId) {
            alert('Please enter a target H3 index');
            return;
        }
        
        moveBtn.disabled = true;
        moveStatus.textContent = 'Moving content...';
        moveStatus.className = 'status-message loading';
        
        try {
            await hexGlobeAPI.moveContent(sourceTileId, targetTileId);
            
            moveStatus.textContent = 'Content moved successfully!';
            moveStatus.className = 'status-message success';
            
            // Refresh source tile data
            const tileData = await hexGlobeAPI.getTile(sourceTileId, true);
            if (tileData) {
                this.updateInfoPanel(tileData, true);
                this.tileView.showTile(tileData);
                document.getElementById('tile-content').value = tileData.content || '';
            }
            
            moveTarget.value = '';
            
            setTimeout(() => {
                moveStatus.textContent = '';
                moveStatus.className = 'status-message';
            }, 3000);
        } catch (error) {
            moveStatus.textContent = `Error: ${error.message}`;
            moveStatus.className = 'status-message error';
            
            setTimeout(() => {
                moveStatus.textContent = '';
                moveStatus.className = 'status-message';
            }, 5000);
        }
        
        moveBtn.disabled = false;
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
