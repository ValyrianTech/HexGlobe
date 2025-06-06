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
        h3LibraryCheckMaxRetries: 10, // Maximum number of retries for H3 library check
        h3LibraryCheckInterval: 100   // Interval in ms between H3 library checks
    },
    
    // State
    state: {
        activeTileId: null, // Will be set from URL or default
        activeTileCoords: { col: 0, row: 0 }, // Will be set to center tile later
        debugMode: true, // Always show debug information
        tiles: [], // Array of tile objects
        zoomLevel: 5 // Default zoom level (1-10)
    },
    
    // Initialize the application
    init: function() {
        console.log("Initializing HexGlobe application...");
        
        // Check if H3 library is available before proceeding
        this.ensureH3LibraryLoaded(() => {
            // Get H3 index from URL query parameter
            this.getH3IndexFromUrl();
            
            // Set up the canvas
            this.setupCanvas();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Generate and render the grid
            this.generateGrid();
            this.render();
            this.updateDebugPanel();
        });
    },
    
    // Ensure the H3 library is loaded before proceeding
    ensureH3LibraryLoaded: function(callback, retryCount = 0) {
        // Check if H3 library is fully loaded and functional
        if (window.h3 && typeof window.h3.isValid === 'function') {
            console.log("H3 library loaded successfully");
            callback();
            return;
        }
        
        // If we've exceeded the maximum retries, use default H3 index
        if (retryCount >= this.config.h3LibraryCheckMaxRetries) {
            console.warn("H3 library not loaded after maximum retries, proceeding with default H3 index");
            this.state.activeTileId = "872830828ffffff";
            callback();
            return;
        }
        
        // Retry after a short delay
        console.log(`Waiting for H3 library to load (attempt ${retryCount + 1}/${this.config.h3LibraryCheckMaxRetries})...`);
        setTimeout(() => {
            this.ensureH3LibraryLoaded(callback, retryCount + 1);
        }, this.config.h3LibraryCheckInterval);
    },
    
    // Get H3 index from URL query parameter
    getH3IndexFromUrl: function() {
        const urlParams = new URLSearchParams(window.location.search);
        const h3Index = urlParams.get('h3');
        
        // Default H3 index to use if none is provided or if the provided one is invalid
        const defaultH3Index = "872830828ffffff";
        
        // Validate the H3 index if provided
        if (h3Index && window.h3 && typeof window.h3.isValid === 'function' && window.h3.isValid(h3Index)) {
            this.state.activeTileId = h3Index;
            console.log(`Using H3 index from URL: ${h3Index}`);
        } else {
            // Use default H3 index
            this.state.activeTileId = defaultH3Index;
            console.log(`Using default H3 index: ${this.state.activeTileId}`);
        }
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

        // Handle zoom slider changes
        document.getElementById("zoom-slider").addEventListener("input", (event) => {
            this.state.zoomLevel = parseInt(event.target.value);
            document.getElementById("zoom-value").textContent = this.state.zoomLevel;
            this.generateGrid();
            this.render();
            this.updateDebugPanel();
        });
    },
    
    // Calculate grid dimensions based on canvas size and zoom level
    calculateGridDimensions: function() {
        const availableWidth = this.canvas.width - (this.config.padding * 2);
        const availableHeight = this.canvas.height - (this.config.padding * 2);
        
        // Calculate hex dimensions
        // Adjust hex size based on zoom level
        // At zoom level 1, hex size is large (active tile takes most of screen)
        // At zoom level 10, hex size is small (many tiles visible)
        const zoomFactor = 1 + (10 - this.state.zoomLevel) * 0.5;
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
        const minRings = this.state.zoomLevel;
        const minTilesForRings = minRings * 2 + 1; // Diameter of the grid in tiles
        
        gridWidth = Math.max(gridWidth, minTilesForRings);
        gridHeight = Math.max(gridHeight, minTilesForRings);
        
        console.log(`Grid dimensions: ${gridWidth}x${gridHeight}, hex size: ${adjustedHexSize}, zoom level: ${this.state.zoomLevel}`);
        
        return {
            hexSize: adjustedHexSize,
            gridWidth: gridWidth,
            gridHeight: gridHeight
        };
    },
    
    // Generate a grid of hexagons that fills the available space
    generateGrid: function() {
        this.state.tiles = [];
        
        // Calculate dimensions
        const dimensions = this.calculateGridDimensions();
        const size = dimensions.hexSize;
        const width = dimensions.gridWidth;
        const height = dimensions.gridHeight;
        
        const hexWidth = size * 2;
        const hexHeight = Math.sqrt(3) * size;
        
        // Calculate offsets to center the grid
        const gridWidthPx = width * (hexWidth * 0.75) + (hexWidth * 0.25);
        const gridHeightPx = height * hexHeight + (hexHeight * 0.5);
        const offsetX = this.centerX - gridWidthPx / 2;
        const offsetY = this.centerY - gridHeightPx / 2;
        
        console.log(`Grid size in pixels: ${gridWidthPx}x${gridHeightPx}`);
        console.log(`Grid offset: ${offsetX},${offsetY}`);
        
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
        
        console.log(`Generated ${this.state.tiles.length} tiles`);
    },
    
    // Handle canvas clicks
    handleCanvasClick: function(x, y) {
        // Check if a tile was clicked
        for (const tile of this.state.tiles) {
            if (tile.hexTile && tile.hexTile.containsPoint(x, y)) {
                console.log(`Clicked on tile: ${tile.id} (${tile.col}, ${tile.row})`);
                
                if (tile.isActive) {
                    // Already the active tile, do nothing
                    return;
                }
                
                // Update the active tile ID
                this.state.activeTileId = tile.id;
                
                // Update URL with the new H3 index without refreshing the page
                const url = new URL(window.location);
                url.searchParams.set('h3', tile.id);
                window.history.pushState({}, '', url);
                
                // Regenerate the grid with the new center tile
                this.generateGrid();
                
                // Re-render the canvas
                this.render();
                
                // Update the debug panel
                this.updateDebugPanel();
                
                return;
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
            const visualProperties = tile.isActive ? 
                this.config.activeTileStyles : 
                this.config.normalTileStyles;
                
            const hexTile = new HexTile(tile.id, visualProperties);
            hexTile.calculateVertices(tile.x, tile.y, hexSize);
            
            // Set the H3 index as content to display
            hexTile.content = tile.id;
            
            // Draw the tile
            hexTile.draw(this.ctx);
            
            // Store the HexTile object for later reference (e.g., for hit detection)
            tile.hexTile = hexTile;
        }
    },
    
    // Update the tile information panel
    updateDebugPanel: function() {
        const debugPanel = document.getElementById("tile-info");
        
        // Always show tile info as debug mode is now always on
        debugPanel.style.display = "block";
        
        // Get the active tile
        const activeTile = this.state.tiles.find(tile => tile.isActive);
        
        if (!activeTile) {
            debugPanel.textContent = "No active tile selected";
            return;
        }
        
        // Format the tile information
        const debugInfo = `
Active Tile:
H3 Index: ${activeTile.id}
Center X,Y: ${Math.round(activeTile.center.x)}, ${Math.round(activeTile.center.y)}
Hex Size: ${Math.round(activeTile.size)}
Grid Size: ${this.state.tiles.length} tiles
Zoom Level: ${this.state.zoomLevel}
Canvas Size: ${this.canvas.width} x ${this.canvas.height}
        `;
        
        debugPanel.textContent = debugInfo;
    }
};

// Initialize the application when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    window.hexGlobeApp.init();
});
