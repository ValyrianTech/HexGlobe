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
        hexSize: 30  // Default hex size that will be adjusted based on canvas size
    },
    
    // State
    state: {
        activeTileCoords: { col: 0, row: 0 }, // Will be set to center tile later
        debugMode: true,
        tiles: [] // Array of tile objects
    },
    
    // Initialize the application
    init: function() {
        console.log("Initializing HexGlobe application...");
        
        // Set up the canvas
        this.setupCanvas();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Generate and render the grid
        this.generateGrid();
        this.render();
        this.updateDebugPanel();
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
        
        // Create the grid
        for (let row = 0; row < height; row++) {
            for (let col = 0; col < width; col++) {
                // Calculate the center position of this hexagon
                const x = offsetX + col * (hexWidth * 0.75) + (hexWidth / 2);
                const y = offsetY + row * hexHeight + (hexHeight / 2) + (col % 2 === 0 ? 0 : hexHeight / 2);
                
                // Create a unique ID for this tile
                const id = `tile-${col}-${row}`;
                
                // Create the tile object
                const tile = {
                    id: id,
                    col: col,
                    row: row,
                    x: x,
                    y: y,
                    isActive: false
                };
                
                // Add the tile to the array
                this.state.tiles.push(tile);
            }
        }
        
        // Set the center tile as active
        const centerCol = Math.floor(width / 2);
        const centerRow = Math.floor(height / 2);
        this.state.activeTileCoords = { col: centerCol, row: centerRow };
        
        // Update the active state of all tiles
        for (const tile of this.state.tiles) {
            tile.isActive = (tile.col === centerCol && tile.row === centerRow);
        }
        
        console.log(`Generated ${this.state.tiles.length} tiles`);
    },
    
    // Handle canvas clicks
    handleCanvasClick: function(x, y) {
        // Check if a tile was clicked
        for (const tile of this.state.tiles) {
            if (tile.hexTile && tile.hexTile.containsPoint(x, y)) {
                console.log(`Clicked on tile: ${tile.id} (${tile.col}, ${tile.row})`);
                
                // Update the active tile coordinates
                this.state.activeTileCoords = { col: tile.col, row: tile.row };
                
                // Update the active state of all tiles
                for (const t of this.state.tiles) {
                    t.isActive = (t.col === tile.col && t.row === tile.row);
                }
                
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
            // Create a HexTile object
            const hexTile = new HexTile(tile.id);
            hexTile.calculateVertices(tile.x, tile.y, hexSize);
            hexTile.setActive(tile.isActive);
            
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
