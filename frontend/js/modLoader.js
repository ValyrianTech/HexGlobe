/**
 * modLoader.js - Module for loading HexGlobe mods
 * 
 * This module handles loading mods based on URL parameters,
 * with fallback to the default mod if loading fails.
 */

class ModLoader {
    /**
     * Create a new ModLoader instance
     * @param {Object} options - Configuration options
     */
    constructor(options = {}) {
        this.options = {
            modsBasePath: options.modsBasePath || './mods',
            defaultMod: options.defaultMod || 'default',
            ...options
        };
        
        this.currentMod = null;
        this.manifest = null;
        this.initialized = false;
    }

    /**
     * Initialize the mod loader
     * @returns {Promise} - Promise that resolves when initialization is complete
     */
    async initialize() {
        try {
            // Get mod name from URL parameter
            const modName = this.getModNameFromUrl();
            console.log(`ModLoader: Initializing with mod "${modName}"`);
            
            // Load the mod
            await this.loadMod(modName);
            
            // Set initialized flag
            this.initialized = true;
            
            // Dispatch event to notify that the mod has been loaded
            this.dispatchModLoadedEvent();
            
            return true;
        } catch (error) {
            console.error("ModLoader: Failed to initialize:", error);
            
            // Try to load the default mod if the specified mod failed
            if (this.currentMod !== this.options.defaultMod) {
                console.warn(`ModLoader: Falling back to default mod "${this.options.defaultMod}"`);
                try {
                    await this.loadMod(this.options.defaultMod);
                    this.initialized = true;
                    this.dispatchModLoadedEvent();
                    return true;
                } catch (fallbackError) {
                    console.error("ModLoader: Failed to load default mod:", fallbackError);
                    return false;
                }
            }
            
            return false;
        }
    }

    /**
     * Get mod name from URL parameter
     * @returns {string} - The mod name from URL or default
     */
    getModNameFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('mod_name') || this.options.defaultMod;
    }

    /**
     * Load a mod by name
     * @param {string} modName - The name of the mod to load
     * @returns {Promise} - Promise that resolves when the mod is loaded
     */
    async loadMod(modName) {
        // Load the manifest
        this.manifest = await this.loadManifest(modName);
        
        // Set current mod
        this.currentMod = modName;
        
        // Load the CSS theme
        await this.loadCss(modName, this.manifest.theme);
        
        // Load the JavaScript
        await this.loadJs(modName, this.manifest.script);
        
        console.log(`ModLoader: Successfully loaded mod "${modName}"`);
        return true;
    }

    /**
     * Load the manifest file for a mod
     * @param {string} modName - The name of the mod
     * @returns {Promise<Object>} - Promise that resolves to the manifest object
     */
    async loadManifest(modName) {
        const manifestUrl = `${this.options.modsBasePath}/${modName}/manifest.json`;
        console.log(`ModLoader: Loading manifest from ${manifestUrl}`);
        
        const response = await fetch(manifestUrl);
        
        if (!response.ok) {
            throw new Error(`Failed to load manifest for mod "${modName}": ${response.statusText}`);
        }
        
        return await response.json();
    }

    /**
     * Load CSS for a mod
     * @param {string} modName - The name of the mod
     * @param {string} cssPath - The path to the CSS file relative to the mod directory
     * @returns {Promise} - Promise that resolves when the CSS is loaded
     */
    async loadCss(modName, cssPath) {
        return new Promise((resolve, reject) => {
            const fullPath = `${this.options.modsBasePath}/${modName}/${cssPath}`;
            console.log(`ModLoader: Loading CSS from ${fullPath}`);
            
            // Check if a link with this mod's ID already exists
            const existingLink = document.getElementById(`mod-${modName}-css`);
            if (existingLink) {
                existingLink.remove();
            }
            
            // Create a new link element
            const link = document.createElement('link');
            link.id = `mod-${modName}-css`;
            link.rel = 'stylesheet';
            link.href = fullPath;
            
            // Set up event handlers
            link.onload = () => {
                console.log(`ModLoader: CSS loaded successfully from ${fullPath}`);
                resolve();
            };
            
            link.onerror = () => {
                const error = new Error(`Failed to load CSS for mod "${modName}" from ${fullPath}`);
                console.error(error);
                reject(error);
            };
            
            // Add the link to the document head
            document.head.appendChild(link);
        });
    }

    /**
     * Load JavaScript for a mod
     * @param {string} modName - The name of the mod
     * @param {string} jsPath - The path to the JavaScript file relative to the mod directory
     * @returns {Promise} - Promise that resolves when the JavaScript is loaded
     */
    async loadJs(modName, jsPath) {
        return new Promise((resolve, reject) => {
            const fullPath = `${this.options.modsBasePath}/${modName}/${jsPath}`;
            console.log(`ModLoader: Loading JavaScript from ${fullPath}`);
            
            // Check if a script with this mod's ID already exists
            const existingScript = document.getElementById(`mod-${modName}-js`);
            if (existingScript) {
                existingScript.remove();
            }
            
            // Create a new script element
            const script = document.createElement('script');
            script.id = `mod-${modName}-js`;
            script.src = fullPath;
            
            // Set up event handlers
            script.onload = () => {
                console.log(`ModLoader: JavaScript loaded successfully from ${fullPath}`);
                resolve();
            };
            
            script.onerror = () => {
                const error = new Error(`Failed to load JavaScript for mod "${modName}" from ${fullPath}`);
                console.error(error);
                reject(error);
            };
            
            // Add the script to the document body
            document.body.appendChild(script);
        });
    }

    /**
     * Dispatch an event to notify that a mod has been loaded
     */
    dispatchModLoadedEvent() {
        const event = new CustomEvent('modLoaded', {
            detail: {
                modName: this.currentMod,
                manifest: this.manifest
            }
        });
        
        document.dispatchEvent(event);
        console.log(`ModLoader: Dispatched modLoaded event for mod "${this.currentMod}"`);
    }

    /**
     * Get the current mod name
     * @returns {string} - The name of the currently loaded mod
     */
    getModName() {
        return this.currentMod;
    }

    /**
     * Get the current mod manifest
     * @returns {Object} - The manifest of the currently loaded mod
     */
    getManifest() {
        return this.manifest;
    }

    /**
     * Check if the mod loader is initialized
     * @returns {boolean} - True if the mod loader is initialized
     */
    isInitialized() {
        return this.initialized;
    }

    /**
     * Construct an API URL with the mod_name parameter
     * @param {string} baseUrl - The base API URL
     * @param {string} endpoint - The API endpoint
     * @returns {string} - The full API URL with mod_name parameter
     */
    getApiUrl(baseUrl, endpoint) {
        const url = new URL(`${baseUrl}/${endpoint}`);
        url.searchParams.set('mod_name', this.currentMod);
        return url.toString();
    }
}

// Create a global instance of the mod loader
window.modLoader = new ModLoader();

// Initialize the mod loader when the DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    await window.modLoader.initialize();
});
