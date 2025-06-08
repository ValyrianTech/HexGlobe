/**
 * HexTile.js - Module for canvas-based hexagon rendering
 * 
 * This module handles the rendering of hexagonal tiles using HTML5 Canvas.
 */

// Load the hex map placeholder image
const hexMapImage = new Image();
hexMapImage.src = 'assets/hex_map_placeholder.png';
let hexMapImageLoaded = false;
hexMapImage.onload = () => {
    hexMapImageLoaded = true;
    console.log('Hex map placeholder image loaded successfully');
};

class HexTile {
    /**
     * Create a new HexTile instance
     * @param {string} id - The H3 index of the tile
     * @param {Object} visualProperties - Visual properties for rendering
     */
    constructor(id, visualProperties = {}) {
        this.id = id;
        this.content = id;
        this.visualProperties = {
            borderColor: "#000000",
            borderThickness: 2,
            borderStyle: "solid",
            fillColor: "#a3c9e9",
            activeFillColor: "#3498db",
            ...visualProperties
        };
        
        this.center = { x: 0, y: 0 };
        this.vertices = [];
        this.size = 0;
        this.isActive = false;
    }

    /**
     * Calculate the vertices of the hexagon
     * @param {number} centerX - X coordinate of the center
     * @param {number} centerY - Y coordinate of the center
     * @param {number} size - Size of the hexagon (distance from center to vertex)
     */
    calculateVertices(centerX, centerY, size) {
        this.center = { x: centerX, y: centerY };
        this.size = size;
        this.vertices = [];

        // Try a different approach: start with angle 0 for flat-bottom orientation
        for (let i = 0; i < 6; i++) {
            const angle = (Math.PI / 3) * i;  // No offset, start at 0
            const x = centerX + size * Math.cos(angle);
            const y = centerY + size * Math.sin(angle);
            this.vertices.push({ x, y });
        }
        
        // Debug log for the first hexagon created
        if (this.id === "8a194da9a74ffff" || this.id === "8a194da9a297fff") {
            console.log(`Hexagon ${this.id} vertices:`, this.vertices);
            console.log(`Hexagon ${this.id} center:`, this.center);
            console.log(`Hexagon ${this.id} size:`, this.size);
            console.log(`Hexagon ${this.id} orientation: 0 (no offset)`);
        }
    }

    /**
     * Draw the hexagon on the canvas
     * @param {CanvasRenderingContext2D} ctx - The canvas rendering context
     */
    draw(ctx) {
        if (this.vertices.length === 0) return;

        // Begin path for the hexagon shape
        ctx.beginPath();
        ctx.moveTo(this.vertices[0].x, this.vertices[0].y);
        
        for (let i = 1; i < this.vertices.length; i++) {
            ctx.lineTo(this.vertices[i].x, this.vertices[i].y);
        }
        
        ctx.closePath();
        
        // Create a clipping path for the hexagon
        ctx.save();
        ctx.clip();
        
        // Draw the background image if loaded
        if (hexMapImageLoaded) {
            // Calculate the position and size to draw the image
            // Use a larger size to ensure the image covers the entire hexagon
            const imgSize = this.size * 3;
            const imgX = this.center.x - imgSize / 2;
            const imgY = this.center.y - imgSize / 2;
            
            // Draw the image
            ctx.drawImage(hexMapImage, imgX, imgY, imgSize, imgSize);
        } else {
            // Fallback to solid color if image not loaded
            ctx.fillStyle = this.isActive ? 
                (this.visualProperties.activeFillColor || this.visualProperties.fillColor) : 
                this.visualProperties.fillColor;
            ctx.fill();
        }
        
        ctx.restore();
        
        // Draw the border
        ctx.strokeStyle = this.visualProperties.borderColor;
        ctx.lineWidth = this.visualProperties.borderThickness;
        ctx.stroke();
        
        // Draw the H3 index in the center
        this.drawH3Index(ctx);
    }
    
    /**
     * Draw the H3 index on the hexagon
     * @param {CanvasRenderingContext2D} ctx - The canvas rendering context
     */
    drawH3Index(ctx) {
        if (!this.content) return;
        
        ctx.save();
        ctx.fillStyle = "#000";
        
        // Calculate font size based on hexagon size
        // Use a smaller font size to fit the full H3 index
        const fontSize = Math.max(6, Math.min(10, this.size / 5));
        ctx.font = `${fontSize}px monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        
        // Handle multi-line content (coordinates and ID)
        if (this.content.includes('\n')) {
            const lines = this.content.split('\n');
            const lineHeight = fontSize * 1.2;
            
            // Draw coordinates on first line
            ctx.fillText(lines[0], this.center.x, this.center.y - lineHeight/2);
            
            // Draw ID on second line
            ctx.fillText(lines[1], this.center.x, this.center.y + lineHeight/2);
        } else {
            // Fallback for single line content
            ctx.fillText(this.content, this.center.x, this.center.y);
        }
        
        ctx.restore();
    }
    
    /**
     * Check if a point is inside the hexagon
     * @param {number} x - X coordinate of the point
     * @param {number} y - Y coordinate of the point
     * @returns {boolean} - True if the point is inside the hexagon
     */
    containsPoint(x, y) {
        if (this.vertices.length === 0) return false;
        
        // Simple distance check as a quick test
        const distanceSquared = (x - this.center.x) ** 2 + (y - this.center.y) ** 2;
        if (distanceSquared > this.size ** 2) return false;
        
        // More accurate point-in-polygon test
        let inside = false;
        for (let i = 0, j = this.vertices.length - 1; i < this.vertices.length; j = i++) {
            const xi = this.vertices[i].x;
            const yi = this.vertices[i].y;
            const xj = this.vertices[j].x;
            const yj = this.vertices[j].y;
            
            const intersect = ((yi > y) !== (yj > y)) && 
                (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
                
            if (intersect) inside = !inside;
        }
        
        return inside;
    }
    
    /**
     * Set the active state of the tile
     * @param {boolean} isActive - Whether the tile is active
     */
    setActive(isActive) {
        this.isActive = isActive;
    }
}
