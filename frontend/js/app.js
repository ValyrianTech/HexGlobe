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
        }
    },
    
    // State
    state: {
        activeTileId: null, // Will be set from URL or default
        activeTileCoords: { col: 0, row: 0 }, // Will be set to center tile later
        debugMode: true,
        tiles: [] // Array of tile objects
    },
    
    // Initialize the application
    init: function() {
        console.log("Initializing HexGlobe application...");
        
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
    },
    
    // Get H3 index from URL query parameter
    getH3IndexFromUrl: function() {
        const urlParams = new URLSearchParams(window.location.search);
        const h3Index = urlParams.get('h3');
        
        // Validate the H3 index if provided
        if (h3Index && window.h3 && window.h3.isValid(h3Index)) {
            this.state.activeTileId = h3Index;
            console.log(`Using H3 index from URL: ${h3Index}`);
        } else {
            // Default to resolution 7 hexagon near the center of the world
            this.state.activeTileId = "872830828ffffff";
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
        // Toggle debug mode
        document.getElementById("toggle-debug").addEventListener("click", () => {
            this.state.debugMode = !this.state.debugMode;
            this.render();
            this.updateDebugPanel();
        });
        
        // Handle canvas clicks
        this.canvas.addEventListener("click", (event) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            this.handleCanvasClick(x, y);
        });
    },
    
    // Calculate grid dimensions based on canvas size
    calculateGridDimensions: function() {
        const availableWidth = this.canvas.width - (this.config.padding * 2);
        const availableHeight = this.canvas.height - (this.config.padding * 2);
        
        // Calculate hex dimensions
        const hexHeight = Math.sqrt(3) * this.config.hexSize;
        const hexWidth = this.config.hexSize * 2;
        
        // Calculate how many hexes can fit in the available space
        // We use 0.75 * hexWidth for horizontal spacing because hexes overlap horizontally
        const cols = Math.max(1, Math.floor(availableWidth / (hexWidth * 0.75)));
        const rows = Math.max(1, Math.floor(availableHeight / hexHeight));
        
        // Adjust hex size to better fill the available space if needed
        let adjustedHexSize = this.config.hexSize;
        
        // If we have very few hexes, try to increase the size to fill more space
        if (cols < 8 || rows < 8) {
            const widthBasedSize = availableWidth / (8 * 0.75) / 2;
            const heightBasedSize = availableHeight / 8 / Math.sqrt(3);
            adjustedHexSize = Math.min(widthBasedSize, heightBasedSize);
        }
        
        console.log(`Grid dimensions: ${cols}x${rows}, hex size: ${adjustedHexSize}`);
        
        return {
            hexSize: adjustedHexSize,
            gridWidth: cols,
            gridHeight: rows
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
    
    // Update the debug panel
    updateDebugPanel: function() {
        const tileInfoElement = document.getElementById("tile-info");
        
        if (!tileInfoElement) return;
        
        if (!this.state.debugMode) {
            tileInfoElement.innerHTML = "<p>Debug mode is off</p>";
            return;
        }
        
        let infoHTML = "";
        
        // Active tile information
        const activeTile = this.state.tiles.find(t => t.isActive);
        if (activeTile) {
            infoHTML += `<h4>Active Tile</h4>`;
            infoHTML += `<p>ID: ${activeTile.id}</p>`;
            infoHTML += `<p>Position: (${activeTile.col}, ${activeTile.row})</p>`;
            infoHTML += `<p>Border Color: ${this.config.activeTileStyles.borderColor}</p>`;
            infoHTML += `<p>Border Thickness: ${this.config.activeTileStyles.borderThickness}px</p>`;
        }
        
        // Grid information
        infoHTML += `<h4>Grid Information</h4>`;
        const dimensions = this.calculateGridDimensions();
        infoHTML += `<p>Grid Size: ${dimensions.gridWidth} x ${dimensions.gridHeight}</p>`;
        infoHTML += `<p>Hex Size: ${dimensions.hexSize.toFixed(2)}</p>`;
        infoHTML += `<p>Canvas Size: ${this.canvas.width} x ${this.canvas.height}</p>`;
        infoHTML += `<p>Total Tiles: ${this.state.tiles.length}</p>`;
        
        tileInfoElement.innerHTML = infoHTML;
    }
};

// Initialize the application when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    window.hexGlobeApp.init();
});
