/**
 * HexTile.js - Module for canvas-based hexagon rendering
 * 
 * This module handles the rendering of hexagonal tiles using HTML5 Canvas.
 */

class HexTile {
    /**
     * Create a new HexTile instance
     * @param {string} id - The H3 index of the tile
     * @param {Object} visualProperties - Visual properties for rendering
     */
    constructor(id, visualProperties = {}) {
        this.id = id;
        this.content = "";
        this.visualProperties = {
            borderColor: "#000000",
            borderThickness: 2,
            borderStyle: "solid",
            fillColor: "#FFFFFF",
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

        for (let i = 0; i < 6; i++) {
            const angle = (Math.PI / 3) * i;
            const x = centerX + size * Math.cos(angle);
            const y = centerY + size * Math.sin(angle);
            this.vertices.push({ x, y });
        }
    }

    /**
     * Draw the hexagon on the canvas
     * @param {CanvasRenderingContext2D} ctx - The canvas rendering context
     */
    draw(ctx) {
        if (this.vertices.length === 0) return;

        ctx.beginPath();
        ctx.moveTo(this.vertices[0].x, this.vertices[0].y);
        
        for (let i = 1; i < this.vertices.length; i++) {
            ctx.lineTo(this.vertices[i].x, this.vertices[i].y);
        }
        
        ctx.closePath();
        
        // Fill the hexagon
        ctx.fillStyle = this.isActive ? "#3498db" : "#a3c9e9";
        ctx.fill();
        
        // Draw the border
        ctx.strokeStyle = this.visualProperties.borderColor;
        ctx.lineWidth = this.visualProperties.borderThickness;
        ctx.stroke();
        
        // Draw grid pattern inside the hexagon to simulate map data
        this.drawGridPattern(ctx);
        
        // Draw the H3 index in the center if debug mode is on
        if (window.hexGlobeApp && window.hexGlobeApp.debugMode) {
            this.drawDebugInfo(ctx);
        }
    }
    
    /**
     * Draw a grid pattern inside the hexagon to simulate map data
     * @param {CanvasRenderingContext2D} ctx - The canvas rendering context
     */
    drawGridPattern(ctx) {
        const gridSpacing = this.size / 4;
        
        ctx.save();
        ctx.strokeStyle = "#e0e0e0";
        ctx.lineWidth = 0.5;
        
        // Create a clipping path for the hexagon
        ctx.beginPath();
        ctx.moveTo(this.vertices[0].x, this.vertices[0].y);
        for (let i = 1; i < this.vertices.length; i++) {
            ctx.lineTo(this.vertices[i].x, this.vertices[i].y);
        }
        ctx.closePath();
        ctx.clip();
        
        // Draw horizontal grid lines
        const startY = Math.floor(this.center.y - this.size) - gridSpacing;
        const endY = Math.ceil(this.center.y + this.size) + gridSpacing;
        
        for (let y = startY; y <= endY; y += gridSpacing) {
            ctx.beginPath();
            ctx.moveTo(this.center.x - this.size - gridSpacing, y);
            ctx.lineTo(this.center.x + this.size + gridSpacing, y);
            ctx.stroke();
        }
        
        // Draw vertical grid lines
        const startX = Math.floor(this.center.x - this.size) - gridSpacing;
        const endX = Math.ceil(this.center.x + this.size) + gridSpacing;
        
        for (let x = startX; x <= endX; x += gridSpacing) {
            ctx.beginPath();
            ctx.moveTo(x, this.center.y - this.size - gridSpacing);
            ctx.lineTo(x, this.center.y + this.size + gridSpacing);
            ctx.stroke();
        }
        
        ctx.restore();
    }
    
    /**
     * Draw debug information on the hexagon
     * @param {CanvasRenderingContext2D} ctx - The canvas rendering context
     */
    drawDebugInfo(ctx) {
        ctx.save();
        ctx.fillStyle = "#000";
        ctx.font = `${this.size / 6}px Arial`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        
        // Truncate the H3 index to fit
        const displayId = this.id.length > 8 ? 
            `${this.id.substring(0, 4)}...${this.id.substring(this.id.length - 4)}` : 
            this.id;
            
        ctx.fillText(displayId, this.center.x, this.center.y);
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
