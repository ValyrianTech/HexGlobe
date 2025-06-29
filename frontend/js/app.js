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
        focusTileStyles: {
            borderColor: "#4CAF50",  // Green border for focus tile
            borderThickness: 4,      // Thicker border for focus tile
            fillColor: "#A5D6A7"     // Light green fill for focus tile
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
        selectedTiles: [], // Array to store selected tile IDs
        focusTileId: null // ID of the last selected tile (focus)
    },
    
    // Initialize the application
    init: function() {
        console.log("Initializing HexGlobe application...");
        
        // Set up the canvas
        this.setupCanvas();
        
        // Get H3 index and zoom level from URL query parameters or set defaults
        this.getParametersFromUrl();
        
        console.log(`After URL parsing, active tile ID is: ${this.state.activeTileId}, zoom level: ${this.state.zoomLevel}`);
        
        // Initialize zoom slider with current zoom level
        // Make sure the zoom slider reflects the value from URL parameters
        const zoomSlider = document.getElementById("zoom-slider");
        const zoomValue = document.getElementById("zoom-value");
        
        if (zoomSlider && zoomValue) {
            console.log(`Setting zoom slider UI to: ${this.state.zoomLevel}`);
            zoomSlider.value = this.state.zoomLevel;
            zoomValue.textContent = this.state.zoomLevel;
        } else {
            console.error("Zoom slider or value element not found in DOM");
        }
        
        // Initialize resolution dropdown with current resolution if no URL parameter is provided
        const urlParams = new URLSearchParams(window.location.search);
        const h3Index = urlParams.get('h3');
        if (!h3Index) {
            document.getElementById("resolution-dropdown").value = this.state.resolution;
        }
        
        // Initialize the navigation system
        this.initNavigation();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Generate the initial grid with the zoom level from URL
        this.generateGrid().then(() => {
            this.render();
            this.updateDebugPanel();
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
    
    // Get parameters from URL query parameters
    getParametersFromUrl: function() {
        const urlParams = new URLSearchParams(window.location.search);
        const h3Index = urlParams.get('h3');
        const zoomParam = urlParams.get('zoom');
        
        // Check if both h3 and zoom parameters are missing
        if (!h3Index && !zoomParam) {
            // Default H3 index to use if none is provided
            const defaultH3Index = this.getDefaultH3IndexForResolution(this.state.resolution);
            const defaultZoom = this.state.zoomLevel;
            
            // Construct URL with default parameters
            const url = new URL(window.location);
            url.searchParams.set('h3', defaultH3Index);
            url.searchParams.set('zoom', defaultZoom);
            
            console.log(`No URL parameters found. Redirecting to default tile: ${defaultH3Index} with zoom: ${defaultZoom}`);
            
            // Redirect to the URL with parameters (this will cause a page reload)
            window.location.href = url.toString();
            return; // Stop execution as we're redirecting
        }
        
        // Default H3 index to use if none is provided
        const defaultH3Index = this.getDefaultH3IndexForResolution(this.state.resolution);
        
        // Process H3 index parameter
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
        
        // Process zoom level parameter
        if (zoomParam) {
            const zoomLevel = parseInt(zoomParam);
            if (!isNaN(zoomLevel) && zoomLevel >= 1 && zoomLevel <= 10) {
                this.state.zoomLevel = zoomLevel;
                console.log(`Using zoom level from URL: ${zoomLevel}`);
            } else {
                console.log(`Invalid zoom level in URL: ${zoomParam}, using default: ${this.state.zoomLevel}`);
            }
        } else {
            console.log(`No zoom level in URL, using default: ${this.state.zoomLevel}`);
        }
        
        // Ensure URL reflects the actual parameters being used
        this.updateUrlParameters();
    },
    
    // Update URL parameters without reloading the page
    updateUrlParameters: function() {
        const url = new URL(window.location);
        url.searchParams.set('h3', this.state.activeTileId);
        url.searchParams.set('zoom', this.state.zoomLevel);
        window.history.replaceState({}, '', url);
    },
    
    // Get a default H3 index for a specific resolution
    getDefaultH3IndexForResolution: function(resolution) {
        // These are H3 indexes for different resolutions
        // Each represents the same area but at different resolutions
        const defaultIndexes = {
            0: "801ffffffffffff", // Res 0
            1: "811fbffffffffff", // Res 1
            2: "821fa7fffffffff", // Res 2
            3: "831fa4fffffffff", // Res 3
            4: "841fa45ffffffff", // Res 4
            5: "851fa443fffffff", // Res 5
            6: "861fa441fffffff", // Res 6
            7: "871fa4418ffffff", // Res 7
            8: "881fa44181fffff", // Res 8
            9: "891fa441803ffff", // Res 9
            10: "8a1fa4418007fff", // Res 10
            11: "8b1fa4418000fff", // Res 11
            12: "8c1fa44180001ff", // Res 12
            13: "8d1fa441800003f", // Res 13
            14: "8e1fa4418000007", // Res 14
            15: "8f1fa4418000000"  // Res 15
        };
        
        return defaultIndexes[resolution] || "871fa4418ffffff"; // Default to res 7 if not found
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
                    const resolutionDropdown = document.getElementById("resolution-dropdown");
                    if (resolutionDropdown) {
                        resolutionDropdown.value = newResolution;
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
            
            // Update URL with new zoom level without reloading the page
            this.updateUrlParameters();
            
            // Generate grid and wait for it to complete before rendering
            this.generateGrid().then(() => {
                this.render();
                this.updateDebugPanel();
            });
        });

        // Handle resolution dropdown changes
        document.getElementById("resolution-dropdown").addEventListener("change", (event) => {
            const newResolution = parseInt(event.target.value);
            
            // Only update if resolution actually changed
            if (newResolution !== this.state.resolution) {
                this.state.resolution = newResolution;
                
                // Check if we have resolution_ids from the API
                if (this.state.navigation && 
                    this.state.navigation.activeTile && 
                    this.state.navigation.activeTile.resolution_ids && 
                    this.state.navigation.activeTile.resolution_ids[newResolution]) {
                    
                    // Use the pre-calculated resolution ID from the API
                    const newIndex = this.state.navigation.activeTile.resolution_ids[newResolution];
                    this.state.activeTileId = newIndex;
                    
                    console.log(`Updated H3 index to resolution ${this.state.resolution} using API data: ${newIndex}`);
                    
                    // Update URL to reflect the new H3 index and preserve zoom level
                    const url = new URL(window.location);
                    url.searchParams.set('h3', newIndex);
                    url.searchParams.set('zoom', this.state.zoomLevel);
                    window.location.href = url.toString(); // This will reload the page with the new URL
                } else {
                    // Use default index if resolution_ids not available
                    this.state.activeTileId = this.getDefaultH3IndexForResolution(this.state.resolution);
                    
                    // Update URL and reload the page, preserving zoom level
                    const url = new URL(window.location);
                    url.searchParams.set('h3', this.state.activeTileId);
                    url.searchParams.set('zoom', this.state.zoomLevel);
                    window.location.href = url.toString(); // This will reload the page with the new URL
                }
            }
        });
        
        // Handle Go To button clicks
        document.getElementById("goto-button").addEventListener("click", () => {
            this.handleGoToInput();
        });
        
        // Also handle Enter key in the input field
        document.getElementById("goto-input").addEventListener("keypress", (event) => {
            if (event.key === "Enter") {
                this.handleGoToInput();
            }
        });
    },
    
    // Handle Go To input processing
    handleGoToInput: function() {
        const input = document.getElementById("goto-input").value.trim();
        
        if (!input) {
            alert("Please enter an H3 index or address");
            return;
        }
        
        // Check if input is an H3 index (hexadecimal characters only)
        const isH3Index = /^[0-9a-fA-F]+$/.test(input);
        
        if (isH3Index) {
            console.log(`Navigating to H3 index: ${input}`);
            // Update URL to navigate to the H3 index, preserving zoom level
            const url = new URL(window.location);
            url.searchParams.set('h3', input);
            url.searchParams.set('zoom', this.state.zoomLevel);
            window.location.href = url.toString(); // This will reload the page with the new URL
        } else {
            console.log(`Geocoding address: ${input}`);
            
            // Show loading indicator
            const gotoButton = document.getElementById("goto-button");
            const originalButtonText = gotoButton.textContent;
            gotoButton.textContent = "Loading...";
            gotoButton.disabled = true;
            
            // Call our backend geocoding API
            const apiUrl = `http://localhost:8000/api/geocode/?address=${encodeURIComponent(input)}&resolution=${this.state.resolution}`;
            
            fetch(apiUrl)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("Geocoding successful:", data);
                    
                    if (data.h3_index) {
                        // Navigate to the returned H3 index, preserving zoom level
                        const url = new URL(window.location);
                        url.searchParams.set('h3', data.h3_index);
                        url.searchParams.set('zoom', this.state.zoomLevel);
                        window.location.href = url.toString();
                    } else {
                        throw new Error("No H3 index returned from geocoding service");
                    }
                })
                .catch(error => {
                    console.error("Error geocoding address:", error);
                    alert(`Error geocoding address: ${error.message}`);
                })
                .finally(() => {
                    // Reset button state
                    gotoButton.textContent = originalButtonText;
                    gotoButton.disabled = false;
                });
        }
    },
    
    // Calculate grid dimensions based on canvas size and zoom level
    calculateGridDimensions: function() {
        const availableWidth = this.canvas.width - (this.config.padding * 2);
        const availableHeight = this.canvas.height - (this.config.padding * 2);
        
        // Calculate hex dimensions based on zoom level
        // At zoom level 1, only show the active tile (80% of canvas)
        // At zoom level 2, show active tile + 1 ring (3 hexagons in diameter)
        // At zoom level 3, show active tile + 2 rings (5 hexagons in diameter)
        // And so on...
        
        let adjustedHexSize;
        let gridWidth, gridHeight;
        
        // Calculate the number of rings based on zoom level
        // Zoom level 1: 0 rings (just the active tile)
        // Zoom level 2: 1 ring
        // Zoom level 3: 2 rings
        // And so on...
        const rings = this.state.zoomLevel - 1;
        
        // Calculate grid dimensions based on rings
        // Diameter = (2 * rings) + 1
        const diameter = rings > 0 ? (2 * rings) + 1 : 1;
        gridWidth = diameter;
        gridHeight = diameter;
        
        // Calculate hex size based on available space and grid dimensions
        // For zoom level 1, make the hex take up 80% of the smaller dimension
        if (this.state.zoomLevel === 1) {
            // For a single hex, use 80% of the smaller canvas dimension
            const smallerDimension = Math.min(availableWidth, availableHeight);
            adjustedHexSize = smallerDimension * 0.4; // Radius is half of diameter, 80% = 0.8/2 = 0.4
        } else {
            // For multiple hexes, calculate size based on how many need to fit
            // We use 0.75 * hexWidth for horizontal spacing because hexes overlap horizontally
            const hexWidth = 2; // Normalized width (will be multiplied by size)
            const hexHeight = Math.sqrt(3); // Normalized height (will be multiplied by size)
            
            // Calculate the maximum size that will fit the grid
            const maxWidthSize = availableWidth / ((gridWidth - 0.25) * 0.75 * hexWidth);
            const maxHeightSize = availableHeight / (gridHeight * hexHeight);
            
            // Use the smaller of the two to ensure the grid fits
            adjustedHexSize = Math.min(maxWidthSize, maxHeightSize);
        }
        
        console.log(`Grid dimensions: ${gridWidth}x${gridHeight}, hex size: ${adjustedHexSize}, zoom level: ${this.state.zoomLevel}, rings: ${rings}, resolution: ${this.state.resolution}`);
        
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
            // Use the calculated grid dimensions based on zoom level
            let apiGridWidth = width;
            let apiGridHeight = height;
            
            console.log(`Fetching grid data for dimensions: ${apiGridWidth}x${apiGridHeight}, zoom level: ${this.state.zoomLevel}`);
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
                
                // Get the tile data from the API response if available
                let tileData = null;
                if (isCenter && gridData.center_tile_data) {
                    // If this is the center tile and we have center tile data
                    tileData = gridData.center_tile_data;
                } else if (gridData.tile_data && gridData.tile_data[h3Index]) {
                    // If we have tile data for this specific H3 index
                    tileData = gridData.tile_data[h3Index];
                }
                
                // Create the tile object
                const tile = {
                    id: h3Index,
                    col: col,
                    row: row,
                    x: x,
                    y: y,
                    isActive: isCenter,
                    isPentagon: isPentagon,
                    tileData: tileData
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
                    
                    // If we unselected the focus tile, set focus to the last selected tile or null if none
                    if (this.state.focusTileId === tile.id) {
                        this.state.focusTileId = this.state.selectedTiles.length > 0 ? 
                            this.state.selectedTiles[this.state.selectedTiles.length - 1] : null;
                        console.log(`Focus tile updated to: ${this.state.focusTileId}`);
                    }
                } else {
                    // Tile is not selected, select it
                    this.state.selectedTiles.push(tile.id);
                    tile.hexTile.setSelected(true);
                    console.log(`Selected tile: ${tile.id}`);
                    
                    // Set this as the focus tile (last selected)
                    this.state.focusTileId = tile.id;
                    console.log(`Focus tile set to: ${this.state.focusTileId}`);
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
        let tileContent = "";
        let backendResolution = "N/A";
        
        if (this.state.navigation && this.state.navigation.activeTile) {
            const navTile = this.state.navigation.activeTile;
            tileContent = navTile.content || "";
            backendResolution = navTile.resolution !== undefined ? navTile.resolution : "N/A";
        }
        
        // Get focus tile color from config
        const focusColor = this.config.focusTileStyles.borderColor;
        
        // Create selected tiles list HTML
        let selectedTilesHtml = '';
        if (this.state.selectedTiles.length > 0) {
            selectedTilesHtml = `<p><strong>Selected Tiles (${this.state.selectedTiles.length}):</strong></p><ul style="max-height: 100px; overflow-y: auto; margin-top: 5px;">${this.state.selectedTiles.map(tileId => {
                const isFocus = tileId === this.state.focusTileId;
                return `<li>${tileId}${isFocus ? ` <span style="color: ${focusColor}; font-weight: bold;">(Focus)</span>` : ''}</li>`;
            }).join('')}</ul>`;
        } else {
            selectedTilesHtml = '<p><strong>Selected Tiles:</strong> None</p>';
        }
        
        // Create focus tile container HTML at the top of the debug panel
        let focusTileContainerHtml = '';
        if (this.state.focusTileId) {
            focusTileContainerHtml = `<div class="focus-tile-container"><span>Focus: </span><a href="#" id="navigate-to-focus" class="focus-tile-link" title="Click to navigate to this tile"><span style="color: ${focusColor};">${this.state.focusTileId}</span></a></div>`;
            
            // Insert the focus tile container at the top of the debug panel
            const focusContainer = document.getElementById("focus-container");
            if (focusContainer) {
                focusContainer.innerHTML = focusTileContainerHtml;
            }
        } else {
            // Clear the focus container if there's no focus tile
            const focusContainer = document.getElementById("focus-container");
            if (focusContainer) {
                focusContainer.innerHTML = '';
            }
        }
        
        // Create focus tile HTML for the selected tiles section
        let focusTileHtml = '';
        if (this.state.focusTileId) {
            focusTileHtml = `<p><strong>Focus Tile:</strong> <span style="color: ${focusColor};">${this.state.focusTileId}</span></p>`;
        }
        
        // Create generate maps button HTML if any tiles are selected
        let generateMapsButtonHtml = '';
        if (this.state.selectedTiles.length > 0) {
            generateMapsButtonHtml = `<button id="generate-maps" class="action-button">Generate Maps for Selected Tiles</button><div id="map-generation-status" class="status-message"></div>`;
        }
        
        // Create move content HTML
        let moveContentHtml = '';
        moveContentHtml = `<div class="content-move-container"><p><strong>Move Content To:</strong></p><div class="move-input-group"><input type="text" id="move-content-target" class="move-content-target" placeholder="Target H3 index"><button id="move-content-button" class="action-button">Move Content</button></div><div id="move-content-status" class="status-message"></div></div>`;
        
        // Store the current height of the tile info panel before updating
        const prevHeight = tileInfo.offsetHeight;
        
        tileInfo.innerHTML = `<p><strong>H3 Index:</strong> ${activeTile.id}</p><div class="content-edit-container"><p><strong>Content:</strong></p><textarea id="tile-content-editor" class="tile-content-editor">${tileContent}</textarea><button id="update-content-button" class="action-button">Update Content</button><div id="update-content-status" class="status-message"></div></div>${moveContentHtml}${selectedTilesHtml}${generateMapsButtonHtml}`;
        
        // Check if the height changed and trigger a canvas resize if it did
        if (prevHeight !== tileInfo.offsetHeight) {
            // Use setTimeout to ensure the DOM has fully updated
            setTimeout(() => {
                this.resizeCanvas();
                this.render();
            }, 0);
        }
        
        // Add event listener for the update content button
        const updateContentButton = document.getElementById("update-content-button");
        if (updateContentButton) {
            updateContentButton.addEventListener("click", () => {
                const contentEditor = document.getElementById("tile-content-editor");
                const newContent = contentEditor.value;
                const statusElement = document.getElementById("update-content-status");
                
                // Show loading status
                statusElement.textContent = "Updating...";
                statusElement.classList.add("status-updating");
                
                // Use the navigation system to update the tile content
                if (this.state.navigation) {
                    this.state.navigation.updateTileContent(newContent)
                        .then(updatedTile => {
                            // Show success status
                            statusElement.textContent = "Content updated successfully!";
                            statusElement.classList.remove("status-updating");
                            statusElement.classList.add("status-success");
                            
                            // Clear the status message after a delay
                            setTimeout(() => {
                                statusElement.textContent = "";
                                statusElement.classList.remove("status-success");
                            }, 3000);
                        })
                        .catch(error => {
                            // Show error status
                            statusElement.textContent = `Error: ${error.message}`;
                            statusElement.classList.remove("status-updating");
                            statusElement.classList.add("status-error");
                            
                            // Clear the error message after a delay
                            setTimeout(() => {
                                statusElement.textContent = "";
                                statusElement.classList.remove("status-error");
                            }, 5000);
                        });
                } else {
                    // Show error if navigation system is not available
                    statusElement.textContent = "Error: Navigation system not initialized";
                    statusElement.classList.remove("status-updating");
                    statusElement.classList.add("status-error");
                    
                    // Clear the error message after a delay
                    setTimeout(() => {
                        statusElement.textContent = "";
                        statusElement.classList.remove("status-error");
                    }, 5000);
                }
            });
        }
        
        // Add event listener for navigation button if it exists
        const navigateLink = document.getElementById("navigate-to-focus");
        if (navigateLink && this.state.focusTileId) {
            navigateLink.addEventListener("click", (event) => {
                // Prevent default link behavior
                event.preventDefault();
                
                const focusTileId = this.state.focusTileId;
                
                // Update the active tile ID
                this.state.activeTileId = focusTileId;
                
                // Update URL with the new H3 index without refreshing the page
                const url = new URL(window.location);
                url.searchParams.set('h3', focusTileId);
                window.history.pushState({}, '', url);
                
                // Use the navigation system to navigate to the new tile
                if (this.state.navigation) {
                    console.log(`Navigating to focus tile: ${focusTileId} via API`);
                    this.state.navigation.navigateTo(focusTileId).then(() => {
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
        
        // Add event listener for generate maps button if it exists
        const generateMapsButton = document.getElementById("generate-maps");
        if (generateMapsButton) {
            generateMapsButton.addEventListener("click", () => {
                this.generateMapsForSelectedTiles();
            });
        }
        
        // Add event listener for move content button if it exists
        const moveContentButton = document.getElementById("move-content-button");
        if (moveContentButton) {
            moveContentButton.addEventListener("click", () => {
                const targetInput = document.getElementById("move-content-target");
                const targetH3Index = targetInput.value.trim();
                
                if (!targetH3Index) {
                    alert("Please enter a target H3 index");
                    return;
                }
                
                // Use the navigation system to move the content
                if (this.state.navigation) {
                    const contentEditor = document.getElementById("tile-content-editor");
                    const content = contentEditor.value;
                    
                    this.state.navigation.moveContent(targetH3Index)
                        .then(() => {
                            console.log(`Content moved to ${targetH3Index}`);
                            
                            // Show success status
                            const statusElement = document.getElementById("move-content-status");
                            statusElement.textContent = "Content moved successfully!";
                            statusElement.classList.remove("status-updating");
                            statusElement.classList.add("status-success");
                            
                            // Clear the status message after a delay
                            setTimeout(() => {
                                statusElement.textContent = "";
                                statusElement.classList.remove("status-success");
                            }, 3000);
                            
                            // Clear the input field
                            targetInput.value = "";
                        })
                        .catch(error => {
                            console.error(`Error moving content: ${error}`);
                            
                            // Show error status
                            const statusElement = document.getElementById("move-content-status");
                            statusElement.textContent = `Error: ${error.message}`;
                            statusElement.classList.remove("status-updating");
                            statusElement.classList.add("status-error");
                            
                            // Clear the status message after a delay
                            setTimeout(() => {
                                statusElement.textContent = "";
                                statusElement.classList.remove("status-error");
                            }, 5000);
                        });
                } else {
                    console.error("Navigation system not initialized");
                    alert("Error: Navigation system not initialized");
                }
            });
        }
    },
    
    // Generate maps for selected tiles
    generateMapsForSelectedTiles: function() {
        if (!this.state.selectedTiles.length) {
            return;
        }
        
        const statusElement = document.getElementById("map-generation-status");
        if (statusElement) {
            statusElement.textContent = `Generating maps for ${this.state.selectedTiles.length} tiles...`;
            statusElement.style.color = "#666";
        }
        
        // Keep track of completed and failed generations
        let completed = 0;
        let failed = 0;
        const totalTiles = this.state.selectedTiles.length;
        
        // Process each selected tile
        this.state.selectedTiles.forEach(tileId => {
            // Call the API to generate the map
            fetch(`${this.state.navigation.apiBaseUrl}/tiles/${tileId}/generate-map`, {
                method: 'POST',
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log(`Map generated for tile ${tileId}:`, data);
                completed++;
                this.updateMapGenerationStatus(completed, failed, totalTiles);
            })
            .catch(error => {
                console.error(`Error generating map for tile ${tileId}:`, error);
                failed++;
                this.updateMapGenerationStatus(completed, failed, totalTiles);
            });
        });
    },
    
    // Update the map generation status message
    updateMapGenerationStatus: function(completed, failed, total) {
        const statusElement = document.getElementById("map-generation-status");
        if (statusElement) {
            if (completed + failed === total) {
                if (failed === 0) {
                    statusElement.textContent = `Successfully generated ${completed} maps. Refreshing page...`;
                    statusElement.style.color = "green";
                    
                    // Add a short delay before refreshing to let the user see the success message
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    statusElement.textContent = `Generated ${completed} maps, ${failed} failed.`;
                    statusElement.style.color = "red";
                }
            } else {
                statusElement.textContent = `Progress: ${completed + failed}/${total} tiles processed...`;
                statusElement.style.color = "#666";
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
            
            if (this.state.focusTileId === tile.id) {
                // Focus tile styling (highest priority)
                visualProperties = this.config.focusTileStyles;
            } else if (this.state.selectedTiles.includes(tile.id)) {
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
            
            const hexTile = new HexTile(
                tile.id, 
                visualProperties, 
                tile.tileData, // Pass the tile data
                onImageLoad
            );
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
    },
    
    // Helper method to clear all selections
    clearSelection: function() {
        // Clear the selected tiles array
        this.state.selectedTiles = [];
        
        // Clear the focus tile
        this.state.focusTileId = null;
        
        // Update the visual state of all tiles
        for (const tile of this.state.tiles) {
            if (tile.hexTile) {
                tile.hexTile.setSelected(false);
            }
        }
    }
};

// Initialize the application when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    window.hexGlobeApp.init();
});
