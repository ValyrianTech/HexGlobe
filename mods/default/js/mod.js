/**
 * Default Mod for HexGlobe
 * 
 * This file serves as both the default mod implementation and a template
 * for creating new mods. It demonstrates the key extension points and
 * provides examples of how to interact with the HexGlobe system.
 */

// Mod class that encapsulates all mod functionality
class HexGlobeMod {
    constructor() {
        this.name = 'default';
        this.initialized = false;
        this.activeTileId = null;
        this.selectedTiles = new Set();
    }

    /**
     * Initialize the mod
     * This is called when the mod is loaded
     */
    async initialize() {
        console.log('Initializing default mod');
        
        // Register event handlers
        this.registerEventHandlers();
        
        // Set initialized flag
        this.initialized = true;
        
        // You can perform any additional initialization here
        this.showModInfo();
    }

    /**
     * Register event handlers for HexGlobe events
     * These allow the mod to respond to user interactions
     */
    registerEventHandlers() {
        // Handle tile selection events
        document.addEventListener('hexglobe:tile:selected', (event) => {
            const tileId = event.detail.tileId;
            this.onTileSelected(tileId);
        });

        // Handle tile deselection events
        document.addEventListener('hexglobe:tile:deselected', (event) => {
            const tileId = event.detail.tileId;
            this.onTileDeselected(tileId);
        });

        // Handle active tile change events
        document.addEventListener('hexglobe:tile:active', (event) => {
            const tileId = event.detail.tileId;
            this.onActiveTileChanged(tileId);
        });

        // Handle content change events
        document.addEventListener('hexglobe:content:changed', (event) => {
            const tileId = event.detail.tileId;
            const content = event.detail.content;
            this.onContentChanged(tileId, content);
        });
    }

    /**
     * Called when a tile is selected
     * @param {string} tileId - The H3 index of the selected tile
     */
    onTileSelected(tileId) {
        console.log(`Tile selected: ${tileId}`);
        this.selectedTiles.add(tileId);
        
        // Example: You could implement game-specific logic here
        // For example, in a chess mod, you might highlight valid move targets
    }

    /**
     * Called when a tile is deselected
     * @param {string} tileId - The H3 index of the deselected tile
     */
    onTileDeselected(tileId) {
        console.log(`Tile deselected: ${tileId}`);
        this.selectedTiles.delete(tileId);
        
        // Example: Clean up any UI elements or state related to this tile
    }

    /**
     * Called when the active tile changes
     * @param {string} tileId - The H3 index of the new active tile
     */
    onActiveTileChanged(tileId) {
        console.log(`Active tile changed to: ${tileId}`);
        this.activeTileId = tileId;
        
        // Example: You might load mod-specific data for this tile
        this.loadTileData(tileId);
    }

    /**
     * Called when a tile's content changes
     * @param {string} tileId - The H3 index of the tile
     * @param {string} content - The new content
     */
    onContentChanged(tileId, content) {
        console.log(`Content changed for tile ${tileId}: ${content}`);
        
        // Example: Parse content for mod-specific commands or data
        if (content && content.startsWith('!')) {
            this.handleCommand(tileId, content);
        }
    }

    /**
     * Load tile data from the backend
     * @param {string} tileId - The H3 index of the tile
     */
    async loadTileData(tileId) {
        try {
            // Note: The mod_name parameter is automatically added by the HexGlobe system
            const response = await fetch(`/api/tiles/${tileId}`);
            if (response.ok) {
                const data = await response.json();
                console.log('Tile data loaded:', data);
                // Process the tile data as needed for your mod
            }
        } catch (error) {
            console.error('Error loading tile data:', error);
        }
    }

    /**
     * Example method for handling special commands in tile content
     * @param {string} tileId - The H3 index of the tile
     * @param {string} content - The content containing the command
     */
    handleCommand(tileId, content) {
        // This is just an example of how a mod might parse commands
        // from tile content. You can implement your own command system.
        const parts = content.substring(1).split(' ');
        const command = parts[0].toLowerCase();
        
        switch (command) {
            case 'info':
                this.showModInfo();
                break;
            case 'color':
                if (parts.length > 1) {
                    this.changeHexColor(tileId, parts[1]);
                }
                break;
            default:
                console.log(`Unknown command: ${command}`);
        }
    }

    /**
     * Example method to change a hexagon's color
     * @param {string} tileId - The H3 index of the tile
     * @param {string} color - The color to apply
     */
    async changeHexColor(tileId, color) {
        try {
            // This is an example of how a mod might update visual properties
            // In a real implementation, you would call the appropriate API endpoint
            console.log(`Changing color of tile ${tileId} to ${color}`);
            
            // Example API call (not implemented in core HexGlobe yet)
            // const response = await fetch(`/api/tiles/${tileId}/visual`, {
            //     method: 'PUT',
            //     headers: { 'Content-Type': 'application/json' },
            //     body: JSON.stringify({ fill_color: color })
            // });
        } catch (error) {
            console.error('Error changing hex color:', error);
        }
    }

    /**
     * Show information about the mod in the debug panel
     */
    showModInfo() {
        const debugPanel = document.querySelector('.debug-panel');
        if (debugPanel) {
            // Check if mod info section already exists
            let modInfoSection = document.getElementById('mod-info-section');
            if (!modInfoSection) {
                // Create a new section for mod info
                modInfoSection = document.createElement('div');
                modInfoSection.id = 'mod-info-section';
                modInfoSection.className = 'debug-controls-group';
                
                const heading = document.createElement('h3');
                heading.textContent = 'Mod Information';
                modInfoSection.appendChild(heading);
                
                const modInfo = document.createElement('p');
                modInfo.innerHTML = `
                    <strong>Name:</strong> Default<br>
                    <strong>Version:</strong> 1.0.0<br>
                    <strong>Description:</strong> Default HexGlobe experience
                `;
                modInfoSection.appendChild(modInfo);
                
                // Add to the beginning of the debug panel
                debugPanel.insertBefore(modInfoSection, debugPanel.firstChild);
            }
        }
    }
}

// Create and initialize the mod when the page loads
window.addEventListener('DOMContentLoaded', () => {
    window.hexGlobeMod = new HexGlobeMod();
    window.hexGlobeMod.initialize();
});
