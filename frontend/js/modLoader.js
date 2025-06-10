/**
 * modLoader.js - Mod loading system for HexGlobe
 * 
 * This module handles loading mods based on URL parameters,
 * including their manifest, CSS theme, and JavaScript code.
 */

// Create a namespace for the mod loader
window.hexGlobeModLoader = {
    // Configuration
    config: {
        defaultModName: 'default',
        modsBasePath: '/mods/',
        manifestFile: 'manifest.json'
    },
    
    // State
    state: {
        currentModName: null,
        manifest: null,
        loaded: false,
        error: null
    },
    
    /**
     * Initialize the mod loader
     * @returns {Promise} Resolves when mod is loaded
     */
    init: async function() {
        console.log("Initializing HexGlobe mod loader...");
        
        try {
            // Get mod name from URL or use default
            this.getModNameFromUrl();
            
            // Load the mod manifest
            await this.loadModManifest();
            
            // Load the mod theme CSS
            await this.loadModTheme();
            
            // Load the mod JavaScript
            await this.loadModScript();
            
            this.state.loaded = true;
            console.log(`Mod '${this.state.currentModName}' loaded successfully`);
            
            // Dispatch event that mod is loaded
            const event = new CustomEvent('hexglobe:mod:loaded', {
                detail: {
                    modName: this.state.currentModName,
                    manifest: this.state.manifest
                }
            });
            document.dispatchEvent(event);
            
            return true;
        } catch (error) {
            this.state.error = error.message;
            console.error(`Error loading mod: ${error.message}`);
            
            // If we failed to load a non-default mod, try to load the default mod
            if (this.state.currentModName !== this.config.defaultModName) {
                console.log(`Attempting to load default mod instead of '${this.state.currentModName}'`);
                this.state.currentModName = this.config.defaultModName;
                return this.init(); // Recursive call with default mod
            }
            
            return false;
        }
    },
    
    /**
     * Get mod name from URL query parameter
     */
    getModNameFromUrl: function() {
        const urlParams = new URLSearchParams(window.location.search);
        const modName = urlParams.get('mod_name');
        
        this.state.currentModName = modName || this.config.defaultModName;
        console.log(`Active mod: ${this.state.currentModName}`);
    },
    
    /**
     * Load the mod's manifest.json file
     * @returns {Promise} Resolves when manifest is loaded
     */
    loadModManifest: async function() {
        const manifestUrl = `${this.config.modsBasePath}${this.state.currentModName}/${this.config.manifestFile}`;
        
        try {
            console.log(`Loading manifest from: ${manifestUrl}`);
            const response = await fetch(manifestUrl);
            
            if (!response.ok) {
                throw new Error(`Failed to load manifest for mod '${this.state.currentModName}': ${response.status} ${response.statusText}`);
            }
            
            this.state.manifest = await response.json();
            console.log(`Loaded manifest for mod '${this.state.currentModName}'`, this.state.manifest);
            
            return this.state.manifest;
        } catch (error) {
            console.error(`Error loading mod manifest: ${error.message}`);
            throw new Error(`Failed to load mod '${this.state.currentModName}': ${error.message}`);
        }
    },
    
    /**
     * Load the mod's theme CSS file
     * @returns {Promise} Resolves when CSS is loaded
     */
    loadModTheme: async function() {
        if (!this.state.manifest || !this.state.manifest.theme) {
            console.log(`No theme specified for mod '${this.state.currentModName}'`);
            return;
        }
        
        return new Promise((resolve, reject) => {
            const themeUrl = `${this.config.modsBasePath}${this.state.currentModName}/${this.state.manifest.theme}`;
            console.log(`Loading theme from: ${themeUrl}`);
            
            // Check if theme is already loaded
            const existingLink = document.getElementById(`mod-${this.state.currentModName}-theme`);
            if (existingLink) {
                console.log(`Theme for mod '${this.state.currentModName}' already loaded`);
                resolve();
                return;
            }
            
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = themeUrl;
            link.id = `mod-${this.state.currentModName}-theme`;
            
            link.onload = () => {
                console.log(`Loaded theme for mod '${this.state.currentModName}'`);
                resolve();
            };
            
            link.onerror = () => {
                const error = `Failed to load theme for mod '${this.state.currentModName}'`;
                console.error(error);
                reject(new Error(error));
            };
            
            document.head.appendChild(link);
        });
    },
    
    /**
     * Load the mod's JavaScript file
     * @returns {Promise} Resolves when script is loaded
     */
    loadModScript: async function() {
        if (!this.state.manifest || !this.state.manifest.script) {
            console.log(`No script specified for mod '${this.state.currentModName}'`);
            return;
        }
        
        return new Promise((resolve, reject) => {
            const scriptUrl = `${this.config.modsBasePath}${this.state.currentModName}/${this.state.manifest.script}`;
            console.log(`Loading script from: ${scriptUrl}`);
            
            // Check if script is already loaded
            const existingScript = document.getElementById(`mod-${this.state.currentModName}-script`);
            if (existingScript) {
                console.log(`Script for mod '${this.state.currentModName}' already loaded`);
                resolve();
                return;
            }
            
            const script = document.createElement('script');
            script.src = scriptUrl;
            script.id = `mod-${this.state.currentModName}-script`;
            
            script.onload = () => {
                console.log(`Loaded script for mod '${this.state.currentModName}'`);
                resolve();
            };
            
            script.onerror = () => {
                const error = `Failed to load script for mod '${this.state.currentModName}'`;
                console.error(error);
                reject(new Error(error));
            };
            
            document.body.appendChild(script);
        });
    },
    
    /**
     * Get the current mod name
     * @returns {string} Current mod name
     */
    getCurrentModName: function() {
        return this.state.currentModName;
    },
    
    /**
     * Get the current mod manifest
     * @returns {Object} Current mod manifest
     */
    getModManifest: function() {
        return this.state.manifest;
    },
    
    /**
     * Check if mod is loaded
     * @returns {boolean} True if mod is loaded
     */
    isLoaded: function() {
        return this.state.loaded;
    },
    
    /**
     * Get mod loading error if any
     * @returns {string|null} Error message or null if no error
     */
    getError: function() {
        return this.state.error;
    }
};
