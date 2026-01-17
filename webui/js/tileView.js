/**
 * tileView.js - 2D Tile View renderer for HexGlobe
 * 
 * Renders a selected tile as a 2D hexagon/pentagon with bottom edge horizontal
 */

class TileView2D {
    constructor(canvasId, placeholderId) {
        this.canvas = document.getElementById(canvasId);
        this.placeholder = document.getElementById(placeholderId);
        this.ctx = this.canvas.getContext('2d');
        this.currentTile = null;
        this.textureCache = {};
        
        // Set up resize handler
        window.addEventListener('resize', () => this.render());
    }
    
    /**
     * Show a tile in the 2D view
     * @param {Object} tileData - Tile data from API
     */
    showTile(tileData) {
        if (!tileData) {
            this.clear();
            return;
        }
        
        this.currentTile = tileData;
        
        // Hide placeholder
        if (this.placeholder) {
            this.placeholder.classList.add('hidden');
        }
        
        this.render();
    }
    
    /**
     * Clear the tile view
     */
    clear() {
        this.currentTile = null;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Show placeholder
        if (this.placeholder) {
            this.placeholder.classList.remove('hidden');
        }
    }
    
    /**
     * Render the current tile
     */
    render() {
        if (!this.currentTile) return;
        
        const container = this.canvas.parentElement;
        const containerWidth = container.clientWidth;
        const containerHeight = container.clientHeight;
        
        // Determine number of vertices (hexagon or pentagon)
        const numVertices = this.currentTile.geometry ? this.currentTile.geometry.length : 6;
        const isPentagon = numVertices === 5;
        
        // The hex map images are 1024x1024 with the hexagon vertices at specific positions:
        // Width spans full 1024 (x: 0 to 1024)
        // Height spans 886.8 pixels (y: 68.6 to 955.4)
        // So the actual hexagon aspect ratio is 886.8/1024 = 0.866 (sqrt(3)/2)
        // But the IMAGE is square (1024x1024), so we need to use square canvas
        const hexRatio = isPentagon ? 1.0 : 1.0; // Image is square
        
        // Calculate size to fit container with padding
        const padding = 20;
        const availableWidth = containerWidth - padding * 2;
        const availableHeight = containerHeight - padding * 2;
        
        let canvasSize;
        if (availableWidth <= availableHeight) {
            canvasSize = availableWidth;
        } else {
            canvasSize = availableHeight;
        }
        
        // Set canvas size to match the square hex map image proportions
        this.canvas.width = canvasSize;
        this.canvas.height = canvasSize;
        
        // Generate vertices matching the hex map image coordinates (scaled to canvas size)
        // Original hex map: 1024x1024 with vertices at specific positions
        const vertices = this.generateVerticesFromHexMap(canvasSize, numVertices);
        
        // Check if we have a texture to load
        if (this.currentTile.latest_map) {
            this.renderWithTexture(vertices, this.currentTile.latest_map);
        } else {
            this.renderSolid(vertices);
        }
    }
    
    /**
     * Generate vertices matching the hex map image coordinates
     * The hex map images are 1024x1024 with vertices at specific positions
     * @param {number} canvasSize - Size of the canvas (square)
     * @param {number} numVertices - Number of vertices (5 or 6)
     * @returns {Array} Array of {x, y} vertices
     */
    generateVerticesFromHexMap(canvasSize, numVertices) {
        // Reference points from the hex map generator (1024x1024 image)
        // These are the exact vertex positions in the generated hex map images
        const hexMapVertices = [
            { x: 1024.0, y: 512.0 },   // right middle
            { x: 768.0, y: 955.4 },    // bottom right
            { x: 256.0, y: 955.4 },    // bottom left
            { x: 0.0, y: 512.0 },      // left middle
            { x: 256.0, y: 68.6 },     // top left
            { x: 768.0, y: 68.6 }      // top right
        ];
        
        // Scale factor from 1024 to canvas size
        const scale = canvasSize / 1024;
        
        // Scale vertices to canvas size
        const vertices = [];
        const count = numVertices === 5 ? 5 : 6;
        
        for (let i = 0; i < count; i++) {
            vertices.push({
                x: hexMapVertices[i].x * scale,
                y: hexMapVertices[i].y * scale
            });
        }
        
        return vertices;
    }
    
    /**
     * Generate vertices for a flat-bottom polygon (fallback for non-textured tiles)
     * @param {number} cx - Center X
     * @param {number} cy - Center Y
     * @param {number} size - Size (center to vertex distance)
     * @param {number} numVertices - Number of vertices (5 or 6)
     * @returns {Array} Array of {x, y} vertices
     */
    generateVertices(cx, cy, size, numVertices) {
        const vertices = [];
        // For flat-bottom hexagon, start at 0 degrees (right side)
        // Vertices go: right-middle, bottom-right, bottom-left, left-middle, top-left, top-right
        const startAngle = 0;
        
        for (let i = 0; i < numVertices; i++) {
            const angle = startAngle + (i * 2 * Math.PI / numVertices);
            vertices.push({
                x: cx + size * Math.cos(angle),
                y: cy + size * Math.sin(angle)
            });
        }
        
        return vertices;
    }
    
    /**
     * Render the tile with a solid color
     * @param {Array} vertices - Array of {x, y} vertices
     */
    renderSolid(vertices) {
        const ctx = this.ctx;
        
        // Clear canvas
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw filled polygon
        ctx.beginPath();
        ctx.moveTo(vertices[0].x, vertices[0].y);
        for (let i = 1; i < vertices.length; i++) {
            ctx.lineTo(vertices[i].x, vertices[i].y);
        }
        ctx.closePath();
        
        // Fill with gradient
        const gradient = ctx.createRadialGradient(
            this.canvas.width / 2, this.canvas.height / 2, 0,
            this.canvas.width / 2, this.canvas.height / 2, this.canvas.width / 2
        );
        gradient.addColorStop(0, '#5a7cff');
        gradient.addColorStop(1, '#3a5cd7');
        ctx.fillStyle = gradient;
        ctx.fill();
        
        // Draw border
        ctx.strokeStyle = '#6af';
        ctx.lineWidth = 2;
        ctx.stroke();
    }
    
    /**
     * Render the tile with a texture
     * @param {Array} vertices - Array of {x, y} vertices
     * @param {string} texturePath - Path to texture image
     */
    renderWithTexture(vertices, texturePath) {
        const fullPath = `${CONFIG.hexagon.dataBasePath}/${texturePath}`;
        
        // Check cache
        if (this.textureCache[fullPath]) {
            this.drawTexturedPolygon(vertices, this.textureCache[fullPath]);
            return;
        }
        
        // Load image
        const img = new Image();
        img.onload = () => {
            this.textureCache[fullPath] = img;
            this.drawTexturedPolygon(vertices, img);
        };
        img.onerror = () => {
            console.warn(`Failed to load texture: ${fullPath}`);
            this.renderSolid(vertices);
        };
        img.src = fullPath;
    }
    
    /**
     * Draw a textured polygon
     * @param {Array} vertices - Array of {x, y} vertices
     * @param {HTMLImageElement} img - Texture image
     */
    drawTexturedPolygon(vertices, img) {
        const ctx = this.ctx;
        
        // Clear canvas
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Create clipping path
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(vertices[0].x, vertices[0].y);
        for (let i = 1; i < vertices.length; i++) {
            ctx.lineTo(vertices[i].x, vertices[i].y);
        }
        ctx.closePath();
        ctx.clip();
        
        // Draw image to fill the canvas
        ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
        
        ctx.restore();
        
        // Draw border
        ctx.beginPath();
        ctx.moveTo(vertices[0].x, vertices[0].y);
        for (let i = 1; i < vertices.length; i++) {
            ctx.lineTo(vertices[i].x, vertices[i].y);
        }
        ctx.closePath();
        ctx.strokeStyle = '#6af';
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}
