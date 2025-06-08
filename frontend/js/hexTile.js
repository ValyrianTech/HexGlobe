/**
 * HexTile.js - Module for canvas-based hexagon rendering
 * 
 * This module handles the rendering of hexagonal tiles using HTML5 Canvas.
 */

// Load the hex map placeholder image as fallback
const placeholderImage = new Image();
placeholderImage.src = 'assets/hex_map_placeholder.png';
let placeholderImageLoaded = false;
placeholderImage.onload = () => {
    placeholderImageLoaded = true;
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
        
        // Use the placeholder image by default
        this.hexMapImage = placeholderImage;
        this.hexMapImageLoaded = placeholderImageLoaded;
        
        // Try to load the tile-specific image
        this.loadHexMapImage();
    }

    /**
     * Load the hex map image for this specific tile
     */
    loadHexMapImage() {
        try {
            // Get the resolution from the H3 index
            const resolution = parseInt(this.id[1], 16); // Second character of H3 index indicates resolution
            
            // Create a new image object for this specific tile
            const tileImage = new Image();
            
            // Set up the onload handler before setting the src
            tileImage.onload = () => {
                // Only update the image if it loaded successfully
                this.hexMapImage = tileImage;
                this.hexMapImageLoaded = true;
                console.log(`Hex map image loaded for tile ${this.id}`);
                console.log(`Image dimensions: ${tileImage.width}x${tileImage.height}`);
            };
            
            // Set up the onerror handler to keep using the placeholder
            tileImage.onerror = () => {
                console.warn(`Failed to load hex map image for tile ${this.id}, using placeholder`);
                console.warn(`Attempted to load from path: ${tileImage.src}`);
                // Keep using the placeholder (already set in constructor)
            };
            
            // Construct the path to the hex map image
            // Use a path relative to the frontend directory, similar to the placeholder
            const hexMapPath = `data/hex_maps/res_${resolution}/${this.id.substring(0, 2)}/${this.id.substring(2, 4)}/${this.id.substring(4, 6)}/${this.id.substring(6, 8)}/${this.id.substring(8, 10)}/${this.id.substring(10, 12)}/${this.id.substring(12, 14)}/${this.id}.png`;
            
            // Log the path we're trying to load
            console.log(`Attempting to load hex map image from: ${hexMapPath}`);
            
            // Set the image source after setting up handlers
            tileImage.src = hexMapPath;
        } catch (error) {
            console.error(`Error loading hex map for tile ${this.id}:`, error);
            // Keep using the placeholder (already set in constructor)
        }
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
        if (this.hexMapImageLoaded) {
            // Calculate the position and size to draw the image
            // Use a larger size to ensure the image covers the entire hexagon
            const imgSize = this.size * 3;
            const imgX = this.center.x - imgSize / 2;
            const imgY = this.center.y - imgSize / 2;
            
            console.log(`Drawing image for tile ${this.id} at (${imgX}, ${imgY}) with size ${imgSize}x${imgSize}`);
            console.log(`Image source: ${this.hexMapImage.src}`);
            console.log(`Image complete: ${this.hexMapImage.complete}, naturalWidth: ${this.hexMapImage.naturalWidth}, naturalHeight: ${this.hexMapImage.naturalHeight}`);
            
            // Draw the image
            try {
                ctx.drawImage(this.hexMapImage, imgX, imgY, imgSize, imgSize);
                console.log(`Image drawn successfully for tile ${this.id}`);
            } catch (error) {
                console.error(`Error drawing image for tile ${this.id}:`, error);
                // Fallback to solid color if image drawing fails
                ctx.fillStyle = this.isActive ? 
                    (this.visualProperties.activeFillColor || this.visualProperties.fillColor) : 
                    this.visualProperties.fillColor;
                ctx.fill();
            }
        } else {
            // Fallback to solid color if no images are loaded
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
