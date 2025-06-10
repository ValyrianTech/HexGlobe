/**
 * Test Mod for HexGlobe
 * 
 * This mod demonstrates a custom theme and behavior for testing the mod system.
 */

class HexGlobeMod {
    constructor() {
        this.name = "Test Mod";
        this.version = "1.0.0";
        this.description = "Test mod with different visual styles for testing the mod system";
        this.initialized = false;
        this.activeTile = null;
    }

    /**
     * Initialize the mod
     * @returns {Promise} - Promise that resolves when initialization is complete
     */
    async initialize() {
        console.log('Initializing test mod');
        this.registerEventHandlers();
        this.initialized = true;
        this.showModInfo();
        return true;
    }

    /**
     * Register event handlers for the mod
     */
    registerEventHandlers() {
        // Listen for tile selection events
        document.addEventListener('tileSelected', this.onTileSelected.bind(this));
        
        // Listen for active tile changes
        window.addEventListener('activeTileChanged', this.onActiveTileChanged.bind(this));
        
        // Listen for content updates
        window.addEventListener('tileContentUpdated', this.onTileContentUpdated.bind(this));
        
        console.log('Test mod event handlers registered');
    }

    /**
     * Handle tile selection events
     * @param {CustomEvent} event - The tile selection event
     */
    onTileSelected(event) {
        const tile = event.detail;
        console.log(`Test mod: Tile selected: ${tile.id}`);
        
        // Example: Add a custom class to the selected tile
        const tileElement = document.querySelector(`[data-tile-id="${tile.id}"]`);
        if (tileElement) {
            tileElement.classList.add('test-mod-selected');
        }
    }

    /**
     * Handle active tile changes
     * @param {CustomEvent} event - The active tile changed event
     */
    onActiveTileChanged(event) {
        this.activeTile = event.detail;
        console.log(`Test mod: Active tile changed to ${this.activeTile.id}`);
        
        // Example: Update the UI with custom information
        this.updateActiveTileInfo();
    }

    /**
     * Handle tile content updates
     * @param {CustomEvent} event - The tile content updated event
     */
    onTileContentUpdated(event) {
        const updatedTile = event.detail;
        console.log(`Test mod: Tile content updated for ${updatedTile.id}`);
        
        // Example: Add custom styling to content
        if (updatedTile.content) {
            // This is just an example - in a real mod you might do more here
            console.log(`Test mod: New content is "${updatedTile.content}"`);
        }
    }

    /**
     * Update the UI with active tile information
     */
    updateActiveTileInfo() {
        if (!this.activeTile) return;
        
        // Example: Add custom information to the debug panel
        const debugPanel = document.getElementById('debug-panel');
        if (debugPanel) {
            // Check if our custom info panel already exists
            let infoPanel = document.getElementById('test-mod-info');
            if (!infoPanel) {
                // Create it if it doesn't exist
                infoPanel = document.createElement('div');
                infoPanel.id = 'test-mod-info';
                infoPanel.style.padding = '10px';
                infoPanel.style.margin = '10px 0';
                infoPanel.style.backgroundColor = '#f0e6ff';
                infoPanel.style.border = '2px solid #6a0dad';
                infoPanel.style.borderRadius = '5px';
                debugPanel.appendChild(infoPanel);
            }
            
            // Update the content
            infoPanel.innerHTML = `
                <h3 style="color: #6a0dad; margin: 0 0 10px 0;">Test Mod Info</h3>
                <p>Active Tile: ${this.activeTile.id}</p>
                <p>Content: ${this.activeTile.content || 'No content'}</p>
            `;
        }
    }

    /**
     * Show mod information in the UI
     */
    showModInfo() {
        // Add mod info to the debug panel
        const debugPanel = document.getElementById('debug-panel');
        if (debugPanel) {
            // Create a mod info section
            const modInfo = document.createElement('div');
            modInfo.className = 'mod-info';
            modInfo.style.padding = '10px';
            modInfo.style.margin = '10px 0';
            modInfo.style.backgroundColor = '#fff0f5';
            modInfo.style.border = '2px solid #ff6b6b';
            modInfo.style.borderRadius = '5px';
            
            modInfo.innerHTML = `
                <h3 style="color: #6a0dad; margin: 0 0 10px 0;">${this.name}</h3>
                <p style="margin: 5px 0;">Version: ${this.version}</p>
                <p style="margin: 5px 0;">${this.description}</p>
            `;
            
            // Insert at the top of the debug panel
            if (debugPanel.firstChild) {
                debugPanel.insertBefore(modInfo, debugPanel.firstChild);
            } else {
                debugPanel.appendChild(modInfo);
            }
        }
    }

    /**
     * Example method: Add a custom marker to a tile
     * @param {string} tileId - The ID of the tile to mark
     * @param {string} markerType - The type of marker to add
     */
    addMarker(tileId, markerType = 'default') {
        console.log(`Test mod: Adding ${markerType} marker to tile ${tileId}`);
        
        // This is just an example method that mods could implement
        // In a real mod, this might add a visual indicator to the tile
    }

    /**
     * Example method: Apply a custom effect to the active tile
     * @param {string} effectType - The type of effect to apply
     */
    applyEffect(effectType = 'highlight') {
        if (!this.activeTile) return;
        
        console.log(`Test mod: Applying ${effectType} effect to active tile ${this.activeTile.id}`);
        
        // This is just an example method that mods could implement
        // In a real mod, this might add a visual effect to the active tile
    }
}

// Create and initialize the mod when the page loads
document.addEventListener('modLoaded', (event) => {
    console.log('Test mod loaded event received:', event.detail);
    
    // Create the mod instance
    window.hexGlobeMod = new HexGlobeMod();
    
    // Initialize the mod
    window.hexGlobeMod.initialize();
});
