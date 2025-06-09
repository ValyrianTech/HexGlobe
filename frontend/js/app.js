/**
 * app.js - Main application logic for HexGlobe
 * 
 * This module initializes the application, sets up the canvas,
 * and renders a simple grid of hexagonal tiles.
 */

// Create a namespace for the application
window.hexGlobeApp = {
    // Configuration
    config: {
        padding: 10, // Reduced padding around the grid
        hexSize: 30,  // Default hex size that will be adjusted based on canvas size
        activeTileStyles: {
            borderColor: "#FF5722",  // Orange border for active tile
            borderThickness: 3,      // Thicker border for active tile
            fillColor: "#3498db"     // Blue fill color for active tile
        },
        normalTileStyles: {
            borderColor: "#000000",  // Black border for normal tiles
            borderThickness: 1,      // Normal border thickness
            fillColor: "#a3c9e9"     // Light blue fill color for normal tiles
        },
        selectedTileStyles: {
            borderColor: "#FF9800",  // Orange border for selected tiles
            borderThickness: 2,      // Medium border for selected tiles
            fillColor: "#FFC107"     // Yellow-ish fill for selected tiles
        },
        h3LibraryCheckMaxRetries: 20, // Increased maximum number of retries for H3 library check
        h3LibraryCheckInterval: 200   // Increased interval in ms between H3 library checks
    },
    
    // State
    state: {
        activeTileId: null, // Will be set from URL or default
        activeTileCoords: { col: 0, row: 0 }, // Will be set to center tile later
        debugMode: true, // Always show debug information
        tiles: [], // Array of tile objects
        zoomLevel: 1, // Default zoom level (1-10)
        resolution: 7, // Default H3 resolution (0-15)
        navigation: null, // Will hold the HexNavigation instance
        selectedTiles: [] // Array to store selected tile IDs
    },
    
    // Initialize the application
    init: function() {
        console.log("Initializing HexGlobe application...");
        
        // Check if H3 library is available before proceeding
        this.ensureH3LibraryLoaded(() => {
            // Get H3 index from URL query parameter or set default based on resolution
            this.getH3IndexFromUrl();
            
            console.log(`After URL parsing, active tile ID is: ${this.state.activeTileId}`);
            
            // Initialize resolution slider with current resolution
            document.getElementById("resolution-value").textContent = this.state.resolution;
            document.getElementById("resolution-slider").value = this.state.resolution;
            
            // Initialize zoom slider with current zoom level
            document.getElementById("zoom-value").textContent = this.state.zoomLevel;
            document.getElementById("zoom-slider").value = this.state.zoomLevel;
            
            // Initialize the navigation system
            this.initNavigation();
            
            // Set up the canvas
            this.setupCanvas();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Generate and render the grid
            this.generateGrid().then(() => {
                this.render();
                this.updateDebugPanel();
            });
        });
    },
    
    // Initialize the navigation system
    initNavigation: function() {
        console.log("Initializing navigation system...");
        
        // Create a new HexNavigation instance with the active tile ID
        this.state.navigation = new HexNavigation({
            initialTileId: this.state.activeTileId,
            apiBaseUrl: "http://localhost:8000/api"
        });
        
        console.log(`Navigation system initialized with tile ID: ${this.state.activeTileId}`);
        
        // Initialize the navigation system
        this.state.navigation.initialize().then(success => {
            if (success) {
                console.log("Navigation system initialized successfully");
            } else {
                console.warn("Navigation system initialization failed, using fallback");
            }
        });
    },
    
    // Ensure the H3 library is loaded before proceeding
    ensureH3LibraryLoaded: function(callback, retryCount = 0) {
        // H3 library is disabled, so we'll proceed without it
        console.log("H3 library is disabled. Proceeding with backend-only functionality.");
        callback();
        return;
    },
    
    // Get H3 index from URL query parameter
    getH3IndexFromUrl: function() {
        const urlParams = new URLSearchParams(window.location.search);
        const h3Index = urlParams.get('h3');
        
        // Default H3 index to use if none is provided
        const defaultH3Index = this.getDefaultH3IndexForResolution(this.state.resolution);
        
        if (h3Index) {
            // Use the H3 index from URL
            this.state.activeTileId = h3Index;
            console.log(`Using H3 index from URL: ${h3Index}`);
            
            // We'll get the resolution from the backend when the tile loads
            console.log(`Resolution will be set from backend data when tile loads`);
        } else {
            // Use default H3 index
            this.state.activeTileId = defaultH3Index;
            console.log(`Using default H3 index: ${this.state.activeTileId} (resolution: ${this.state.resolution})`);
        }
        
        // Ensure URL reflects the actual H3 index being used
        const url = new URL(window.location);
        url.searchParams.set('h3', this.state.activeTileId);
        window.history.replaceState({}, '', url);
    },
    
    // Get a default H3 index for a specific resolution
    getDefaultH3IndexForResolution: function(resolution) {
        // These are example H3 indexes for different resolutions
        // Each represents approximately the same area but at different resolutions
        const defaultIndexes = {
            0: "8001fffffffffff", // Res 0
            1: "81007ffffffffff", // Res 1
            2: "820043fffffffff", // Res 2
            3: "83000dfffffffff", // Res 3
            4: "8400013ffffffff", // Res 4
            5: "85000033fffffff", // Res 5
            6: "860000057ffffff", // Res 6
            7: "870000051ffffff", // Res 7 - Updated to a valid index
            8: "880000003ffffff", // Res 8
            9: "890000000ffffff", // Res 9
            10: "8a0000000ffffff", // Res 10
            11: "8b00000003fffff", // Res 11
            12: "8c000000003ffff", // Res 12
            13: "8d0000000003fff", // Res 13
            14: "8e00000000003ff", // Res 14
            15: "8f000000000003f"  // Res 15
        };
        
        return defaultIndexes[resolution] || "870000051ffffff"; // Default to res 7 if not found
    },
    
    // Set up the canvas
    setupCanvas: function() {
        this.canvas = document.getElementById("hexCanvas");
        this.ctx = this.canvas.getContext("2d");
        
        // Set the canvas size to match its container
        this.resizeCanvas();
        
        // Handle window resize
        window.addEventListener("resize", () => {
            this.resizeCanvas();
            this.generateGrid(); // Regenerate grid on resize
            this.render();
        });
    },
    
    // Resize the canvas to match its container
    resizeCanvas: function() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        
        // Update the center point
        this.centerX = this.canvas.width / 2;
        this.centerY = this.canvas.height / 2;
        
        console.log(`Canvas resized to ${this.canvas.width}x${this.canvas.height}`);
    },
    
    // Set up event listeners
    setupEventListeners: function() {
        // Handle canvas clicks
        this.canvas.addEventListener("click", (event) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            this.handleCanvasClick(x, y);
        });

        // Listen for active tile changes from the navigation system
        window.addEventListener("activeTileChanged", (event) => {
            const tileData = event.detail;
            
            // Update resolution from backend data if available
            if (tileData.resolution !== undefined && tileData.resolution !== null) {
                const newResolution = parseInt(tileData.resolution);
                
                if (newResolution !== this.state.resolution) {
                    console.log(`Updating resolution from backend: ${newResolution}`);
                    this.state.resolution = newResolution;
                    
                    // Update UI to reflect the new resolution
                    const resolutionSlider = document.getElementById("resolution-slider");
                    if (resolutionSlider) {
                        resolutionSlider.value = newResolution;
                        document.getElementById("resolution-value").textContent = newResolution;
                    }
                }
            }
            
            // Update debug panel with the new tile data
            this.updateDebugPanel();
        });

        // Handle zoom slider changes
        document.getElementById("zoom-slider").addEventListener("input", (event) => {
            this.state.zoomLevel = parseInt(event.target.value);
            document.getElementById("zoom-value").textContent = this.state.zoomLevel;
            
            // Generate grid with new zoom level
            this.generateGrid().then(() => {
                this.render();
                this.updateDebugPanel();
            });
        });

        // Handle resolution slider changes
        document.getElementById("resolution-slider").addEventListener("input", (event) => {
            const newResolution = parseInt(event.target.value);
            
            // Only update if resolution actually changed
            if (newResolution !== this.state.resolution) {
                this.state.resolution = newResolution;
                document.getElementById("resolution-value").textContent = this.state.resolution;
                
                // Update the active tile ID to use the new resolution
                if (window.h3 && typeof window.h3.h3ToGeo === 'function' && typeof window.h3.geoToH3 === 'function') {
                    try {
                        // Get the lat/lng of the current index
                        const latLng = window.h3.h3ToGeo(this.state.activeTileId);
                        
                        // Convert to the new resolution
                        const newIndex = window.h3.geoToH3(latLng[0], latLng[1], this.state.resolution);
                        this.state.activeTileId = newIndex;
                        
                        console.log(`Updated H3 index to resolution ${this.state.resolution}: ${newIndex}`);
                        
                        // Update URL to reflect the new H3 index
                        const url = new URL(window.location);
                        url.searchParams.set('h3', newIndex);
                        window.history.replaceState({}, '', url);
                        
                        // Update the navigation system with the new active tile ID
                        if (this.state.navigation) {
                            this.state.navigation.navigateTo(newIndex).then(() => {
                                // Generate grid and wait for it to complete before rendering
                                this.generateGrid().then(() => {
                                    this.render();
                                    this.updateDebugPanel();
                                });
                            });
                        } else {
                            // Generate grid and wait for it to complete before rendering
                            this.generateGrid().then(() => {
                                this.render();
                                this.updateDebugPanel();
                            });
                        }
                    } catch (error) {
                        console.error("Error updating H3 resolution:", error);
                        // Fall back to a default index for this resolution
                        this.state.activeTileId = this.getDefaultH3IndexForResolution(this.state.resolution);
                        
                        // Generate grid and wait for it to complete before rendering
                        this.generateGrid().then(() => {
                            this.render();
                            this.updateDebugPanel();
                        });
                    }
                } else {
                    // If H3 functions aren't available, use default index
                    this.state.activeTileId = this.getDefaultH3IndexForResolution(this.state.resolution);
                    
                    // Generate grid and wait for it to complete before rendering
                    this.generateGrid().then(() => {
                        this.render();
                        this.updateDebugPanel();
                    });
                }
            }
        });
    },
    
    // Calculate grid dimensions based on canvas size and zoom level
    calculateGridDimensions: function() {
        const availableWidth = this.canvas.width - (this.config.padding * 2);
        const availableHeight = this.canvas.height - (this.config.padding * 2);
        
        // Calculate hex dimensions
        // Adjust hex size based on zoom level
        // At zoom level 1, hex size is very large (active tile takes most of screen)
        // At zoom level 10, hex size is small (many tiles visible)
        // Using exponential scaling to make zoom level 1 much larger
        let zoomFactor;
        if (this.state.zoomLevel === 1) {
            zoomFactor = 4.5; // Much larger factor for zoom level 1
        } else {
            zoomFactor = 1 + (10 - this.state.zoomLevel) * 0.4;
        }
        
        const baseHexSize = this.config.hexSize;
        const adjustedHexSize = baseHexSize * zoomFactor;
        
        // Calculate how many hexes can fit in the available space
        const hexHeight = Math.sqrt(3) * adjustedHexSize;
        const hexWidth = adjustedHexSize * 2;
        
        // We use 0.75 * hexWidth for horizontal spacing because hexes overlap horizontally
        const cols = Math.max(1, Math.floor(availableWidth / (hexWidth * 0.75)));
        const rows = Math.max(1, Math.floor(availableHeight / hexHeight));
        
        // For zoom level 1, we want to show just the active tile and immediate neighbors
        // For zoom level 10, we want to show at least 10 rings of neighbors
        let gridWidth = cols;
        let gridHeight = rows;
        
        // Ensure we have enough tiles to show the desired number of rings based on zoom level
        // For zoom level 1, show only 1 ring of neighbors
        const minRings = this.state.zoomLevel === 1 ? 1 : this.state.zoomLevel;
        const minTilesForRings = minRings * 2 + 1; // Diameter of the grid in tiles
        
        gridWidth = Math.max(gridWidth, minTilesForRings);
        gridHeight = Math.max(gridHeight, minTilesForRings);
        
        console.log(`Grid dimensions: ${gridWidth}x${gridHeight}, hex size: ${adjustedHexSize}, zoom level: ${this.state.zoomLevel}, resolution: ${this.state.resolution}`);
        
        return {
            hexSize: adjustedHexSize,
            gridWidth: gridWidth,
            gridHeight: gridHeight
        };
    },
    
    // Generate a grid of hexagons that fills the available space
    generateGrid: async function() {
        this.state.tiles = [];
        
        // Calculate dimensions
        const dimensions = this.calculateGridDimensions();
        const size = dimensions.hexSize;
        const width = dimensions.gridWidth;
        const height = dimensions.gridHeight;
        
        // Calculate hex dimensions based on flat-bottom orientation
        const hexWidth = size * 2;
        const hexHeight = Math.sqrt(3) * size;
        
        // Match the spacing used in the test script
        const horizSpacing = 1.5 * size;
        const vertSpacing = hexHeight;
        
        // Fetch grid data from the API
        try {
            // For zoom level 1, limit the grid to 5x5 regardless of calculated dimensions
            let apiGridWidth = width;
            let apiGridHeight = height;
            
            if (this.state.zoomLevel === 1) {
                apiGridWidth = 5;
                apiGridHeight = 5;
                console.log(`Zoom level 1: Limiting grid request to ${apiGridWidth}x${apiGridHeight}`);
            }
            
            console.log(`Fetching grid data for dimensions: ${apiGridWidth}x${apiGridHeight}`);
            const gridData = await this.state.navigation.fetchTileGrid(apiGridWidth, apiGridHeight);
            console.log("Grid data received:", gridData);
            
            // Get the bounds from the grid data
            const bounds = gridData.bounds || {
                min_row: -Math.floor(height/2),
                max_row: Math.floor(height/2),
                min_col: -Math.floor(width/2),
                max_col: Math.floor(width/2)
            };
            
            // Find the active tile's coordinates in the grid
            let activeTileRow = 0;
            let activeTileCol = 0;
            
            // Look for the active tile in the grid
            Object.entries(gridData.grid).forEach(([coordKey, h3Index]) => {
                if (h3Index === gridData.center_tile_id) {
                    const [row, col] = coordKey.split(',').map(Number);
                    activeTileRow = row;
                    activeTileCol = col;
                }
            });
            
            console.log(`Active tile coordinates: (${activeTileCol}, ${activeTileRow})`);
            
            // Calculate the total grid dimensions in pixels
            const gridWidthPx = (bounds.max_col - bounds.min_col + 1) * horizSpacing + (horizSpacing * 0.25);
            const gridHeightPx = (bounds.max_row - bounds.min_row + 1) * vertSpacing + (vertSpacing * 0.5);
            
            // Calculate offsets to center the active tile in the canvas
            // First, calculate the position of the active tile in pixels
            const activeTileX = (activeTileCol - bounds.min_col) * horizSpacing;
            const activeTileY = (activeTileRow - bounds.min_row) * vertSpacing;
            
            // Apply the offset for odd columns (matching the test script)
            const activeColOffset = (activeTileCol % 2 === 1) ? vertSpacing / 2 : 0;
            const activeTileYWithOffset = activeTileY + activeColOffset;
            
            // Then, calculate the offsets needed to center this tile in the canvas
            const offsetX = this.centerX - activeTileX;
            const offsetY = this.centerY - activeTileYWithOffset;
            
            console.log(`Grid size in pixels: ${gridWidthPx}x${gridHeightPx}`);
            console.log(`Grid offset: ${offsetX},${offsetY}`);
            
            // Process each coordinate in the grid object
            Object.entries(gridData.grid).forEach(([coordKey, h3Index]) => {
                // Parse the coordinate key (format: "row,col" from backend)
                const [row, col] = coordKey.split(',').map(Number);
                
                // Calculate the visual position on the canvas
                // Convert from relative grid coordinates to absolute screen coordinates
                const gridCol = col - bounds.min_col;
                const gridRow = row - bounds.min_row;
                
                // Calculate position using the same logic as the test script
                // But invert the y-coordinate calculation to match the visual expectation
                // (negative row should be below, positive row should be above)
                let x = offsetX + gridCol * horizSpacing;
                let y = offsetY + (bounds.max_row - bounds.min_row - gridRow) * vertSpacing;
                
                // Apply offset for odd columns (matching the test script)
                if (col % 2 !== 0) {  
                    y -= vertSpacing / 2;  
                }
                
                // Add debug logging for the bottom neighbor tile
                if (h3Index !== gridData.center_tile_id && row === -1 && col === 0) {
                    console.log("Bottom neighbor tile found!");
                    console.log(`Bottom neighbor coordinates: (${col}, ${row})`);
                    console.log(`Bottom neighbor grid position: (${gridCol}, ${gridRow})`);
                    console.log(`Bottom neighbor pixel position before offset: (${gridCol * horizSpacing}, ${gridRow * vertSpacing})`);
                    console.log(`Bottom neighbor pixel position after offset: (${x}, ${y})`);
                    console.log(`Vertical spacing: ${vertSpacing}, Horizontal spacing: ${horizSpacing}`);
                    console.log(`Active tile position: (${activeTileX}, ${activeTileY + activeColOffset})`);
                    console.log(`Expected vertical distance: ${vertSpacing}`);
                    console.log(`Actual vertical distance: ${Math.abs((activeTileY + activeColOffset) - y)}`);
                }
                
                // Check if this is a pentagon
                const isPentagon = gridData.pentagon_positions && 
                    gridData.pentagon_positions.some(pos => pos[0] === row && pos[1] === col);
                
                // Calculate if this is the center/active tile
                const isCenter = (h3Index === gridData.center_tile_id);
                
                // Create the tile object
                const tile = {
                    id: h3Index,
                    col: col,
                    row: row,
                    x: x,
                    y: y,
                    isActive: isCenter,
                    isPentagon: isPentagon
                };
                
                // Add the tile to the array
                this.state.tiles.push(tile);
                
                // Update active tile coordinates
                if (isCenter) {
                    this.state.activeTileCoords = { col: col, row: row };
                }
            });
            
            console.log(`Generated ${this.state.tiles.length} tiles`);
        } catch (error) {
            console.error("Error generating grid:", error);
            
            // Fallback to the old method if the API fails
            this.generateGridFallback(width, height, size, this.centerX - (width * hexWidth * 0.75) / 2, this.centerY - (height * hexHeight) / 2);
        }
    },
    
    // Fallback grid generation method (original implementation)
    generateGridFallback: function(width, height, size, offsetX, offsetY) {
        console.log("Using fallback grid generation method");
        
        const hexWidth = size * 2;
        const hexHeight = Math.sqrt(3) * size;
        
        // Generate H3 indexes for the grid
        // Start with the center tile (from URL or default)
        const centerCol = Math.floor(width / 2);
        const centerRow = Math.floor(height / 2);
        
        // Create the grid
        for (let row = 0; row < height; row++) {
            for (let col = 0; col < width; col++) {
                // Calculate the center position of this hexagon
                const x = offsetX + col * (hexWidth * 0.75) + (hexWidth / 2);
                const y = offsetY + row * hexHeight + (hexHeight / 2) + (col % 2 === 0 ? 0 : hexHeight / 2);
                
                // Calculate H3 index for this tile
                let h3Index;
                
                if (col === centerCol && row === centerRow) {
                    // This is the center tile, use the active tile ID
                    h3Index = this.state.activeTileId;
                } else {
                    // Calculate the relative position from the center
                    const relCol = col - centerCol;
                    const relRow = row - centerRow;
                    
                    // Use H3 library to get the neighboring indexes
                    // This is a simplified approach - in reality, the grid layout doesn't perfectly match H3 grid
                    try {
                        // For simplicity, we'll use kRing to get a set of neighbors and then pick one based on position
                        const ringSize = Math.max(Math.abs(relCol), Math.abs(relRow));
                        if (ringSize > 0) {
                            const neighbors = window.h3.kRing(this.state.activeTileId, ringSize);
                            
                            // Simple mapping from grid position to neighbor index
                            // This is an approximation and won't perfectly match H3's actual layout
                            const neighborIndex = ((relRow + ringSize) * (2 * ringSize + 1) + (relCol + ringSize)) % neighbors.length;
                            h3Index = neighbors[neighborIndex];
                        } else {
                            h3Index = this.state.activeTileId;
                        }
                    } catch (error) {
                        console.error("Error calculating H3 index:", error);
                        h3Index = `error-${col}-${row}`;
                    }
                }
                
                // Create the tile object
                const tile = {
                    id: h3Index,
                    col: col,
                    row: row,
                    x: x,
                    y: y,
                    isActive: (col === centerCol && row === centerRow)
                };
                
                // Add the tile to the array
                this.state.tiles.push(tile);
            }
        }
        
        // Set the center tile as active
        this.state.activeTileCoords = { col: centerCol, row: centerRow };
        
        console.log(`Generated ${this.state.tiles.length} tiles (fallback method)`);
    },
    
    // Handle canvas clicks
    handleCanvasClick: function(x, y) {
        // Check if a tile was clicked
        for (const tile of this.state.tiles) {
            if (tile.hexTile && tile.hexTile.containsPoint(x, y)) {
                console.log(`Clicked on tile: ${tile.id} (${tile.col}, ${tile.row})`);
                
                // Toggle selection for the clicked tile
                const selectedIndex = this.state.selectedTiles.findIndex(selectedTile => selectedTile === tile.id);
                
                if (selectedIndex >= 0) {
                    // Tile is already selected, unselect it
                    this.state.selectedTiles.splice(selectedIndex, 1);
                    tile.hexTile.setSelected(false);
                    console.log(`Unselected tile: ${tile.id}`);
                } else {
                    // Tile is not selected, select it
                    this.state.selectedTiles.push(tile.id);
                    tile.hexTile.setSelected(true);
                    console.log(`Selected tile: ${tile.id}`);
                }
                
                // Re-render the canvas to show selection changes
                this.render();
                
                // Update the debug panel
                this.updateDebugPanel();
                
                return;
            }
        }
    },
    
    // Update the tile information panel
    updateDebugPanel: function() {
        // Get the active tile
        const activeTile = this.state.tiles.find(tile => tile.isActive);
        
        if (!activeTile) {
            return;
        }
        
        // Update the tile information panel
        const tileInfo = document.getElementById("tile-info");
        
        // Try to get tile data from the navigation system
        let tileContent = "No content available";
        let backendResolution = "N/A";
        
        if (this.state.navigation && this.state.navigation.activeTile) {
            const navTile = this.state.navigation.activeTile;
            tileContent = navTile.content || "No content available";
            backendResolution = navTile.resolution !== undefined ? navTile.resolution : "N/A";
        }
        
        // Create selected tiles list HTML
        let selectedTilesHtml = '';
        if (this.state.selectedTiles.length > 0) {
            selectedTilesHtml = `
                <p><strong>Selected Tiles (${this.state.selectedTiles.length}):</strong></p>
                <ul style="max-height: 100px; overflow-y: auto; margin-top: 5px;">
                    ${this.state.selectedTiles.map(tileId => `<li>${tileId}</li>`).join('')}
                </ul>
            `;
        } else {
            selectedTilesHtml = '<p><strong>Selected Tiles:</strong> None</p>';
        }
        
        // Create navigation button HTML if exactly one tile is selected
        let navigationButtonHtml = '';
        if (this.state.selectedTiles.length === 1) {
            navigationButtonHtml = `
                <button id="navigate-to-selected" class="action-button">
                    Navigate to Selected Tile
                </button>
            `;
        }
        
        tileInfo.innerHTML = `
            <p><strong>H3 Index:</strong> ${activeTile.id}</p>
            <p><strong>Resolution (Backend):</strong> ${backendResolution}</p>
            <p><strong>Resolution (Frontend):</strong> ${this.state.resolution}</p>
            <p><strong>Zoom Level:</strong> ${this.state.zoomLevel}</p>
            <p><strong>Grid Position:</strong> (${activeTile.col}, ${activeTile.row})</p>
            <p><strong>Content:</strong> ${tileContent}</p>
            ${selectedTilesHtml}
            ${navigationButtonHtml}
        `;
        
        // Add event listener for navigation button if it exists
        const navigateButton = document.getElementById("navigate-to-selected");
        if (navigateButton) {
            navigateButton.addEventListener("click", () => {
                const selectedTileId = this.state.selectedTiles[0];
                
                // Update the active tile ID
                this.state.activeTileId = selectedTileId;
                
                // Update URL with the new H3 index without refreshing the page
                const url = new URL(window.location);
                url.searchParams.set('h3', selectedTileId);
                window.history.pushState({}, '', url);
                
                // Use the navigation system to navigate to the new tile
                if (this.state.navigation) {
                    console.log(`Navigating to tile: ${selectedTileId} via API`);
                    this.state.navigation.navigateTo(selectedTileId).then(() => {
                        // Clear the selection
                        this.clearSelection();
                        
                        // Regenerate the grid with the new center tile
                        this.generateGrid().then(() => {
                            // Re-render the canvas
                            this.render();
                            
                            // Update the debug panel
                            this.updateDebugPanel();
                        });
                    });
                } else {
                    console.warn("Navigation system not initialized, using fallback");
                    // Fallback to the old method
                    this.clearSelection();
                    this.generateGrid().then(() => {
                        this.render();
                        this.updateDebugPanel();
                    });
                }
            });
        }
    },
    
    // Helper method to clear all selections
    clearSelection: function() {
        // Clear the selected tiles array
        this.state.selectedTiles = [];
        
        // Update the tile objects
        for (const tile of this.state.tiles) {
            if (tile.hexTile) {
                tile.hexTile.setSelected(false);
            }
        }
    },
    
    // Render the canvas
    render: function() {
        // Clear the canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Get current dimensions
        const dimensions = this.calculateGridDimensions();
        const hexSize = dimensions.hexSize;
        
        console.log(`Rendering with hex size: ${hexSize}`);
        
        // Draw each tile
        for (const tile of this.state.tiles) {
            // Create a HexTile object with appropriate visual properties
            let visualProperties;
            
            if (this.state.selectedTiles.includes(tile.id)) {
                // Selected tile styling
                visualProperties = this.config.selectedTileStyles;
            } else if (tile.isActive) {
                // Active tile styling
                visualProperties = this.config.activeTileStyles;
            } else {
                // Normal tile styling
                visualProperties = this.config.normalTileStyles;
            }
            
            // Define a callback function for when the image loads
            const onImageLoad = (hexTile) => {
                // Store the updated hexTile object with the loaded image
                tile.hexTile = hexTile;
                
                // Redraw just this specific tile with the loaded image
                this.redrawTile(tile, hexSize);
                
                console.log(`Redrawing tile ${tile.id} with loaded image`);
            };
            
            const hexTile = new HexTile(tile.id, visualProperties, onImageLoad);
            hexTile.calculateVertices(tile.x, tile.y, hexSize);
            
            // Set the H3 index as content to display
            // Include the coordinates in the displayed content
            hexTile.content = `(${tile.row},${tile.col})\n${tile.id}`;
            
            // Set active and selected states
            hexTile.setActive(tile.isActive);
            hexTile.setSelected(this.state.selectedTiles.includes(tile.id));
            
            // Draw the tile
            hexTile.draw(this.ctx);
            
            // Store the HexTile object for later reference (e.g., for hit detection)
            tile.hexTile = hexTile;
            
            console.log(`Drawing tile at (${tile.col}, ${tile.row}) with ID ${tile.id}`);
            console.log(`Tile position: x=${tile.x}, y=${tile.y}`);
            console.log(`Tile is${tile.isActive ? '' : ' not'} active`);
            console.log(`Tile is${this.state.selectedTiles.includes(tile.id) ? '' : ' not'} selected`);
        }
    },
    
    // Redraw a specific tile when its image is loaded
    redrawTile: function(tile, hexSize) {
        if (!tile.hexTile) return;
        
        // Recalculate vertices with current position and size
        tile.hexTile.calculateVertices(tile.x, tile.y, hexSize);
        
        // Draw just this tile
        tile.hexTile.draw(this.ctx);
        
        // Redraw the border of any tiles that might have been covered
        // This ensures tile borders remain visible
        this.redrawTileBorders();
    },
    
    // Redraw all tile borders to ensure they're visible
    redrawTileBorders: function() {
        for (const tile of this.state.tiles) {
            if (tile.hexTile && tile.hexTile.vertices.length > 0) {
                const ctx = this.ctx;
                
                // Draw just the border
                ctx.beginPath();
                ctx.moveTo(tile.hexTile.vertices[0].x, tile.hexTile.vertices[0].y);
                
                for (let i = 1; i < tile.hexTile.vertices.length; i++) {
                    ctx.lineTo(tile.hexTile.vertices[i].x, tile.hexTile.vertices[i].y);
                }
                
                ctx.closePath();
                ctx.strokeStyle = tile.hexTile.visualProperties.borderColor;
                ctx.lineWidth = tile.hexTile.visualProperties.borderThickness;
                ctx.stroke();
            }
        }
    }
};

// Initialize the application when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    window.hexGlobeApp.init();
});
