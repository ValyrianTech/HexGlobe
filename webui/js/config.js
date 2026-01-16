/**
 * config.js - Configuration for HexGlobe 3D
 */

const CONFIG = {
    // API Configuration
    api: {
        baseUrl: 'http://localhost:8000/api',
        modName: 'default'
    },
    
    // Globe Configuration
    globe: {
        radius: 1.0,
        segments: 64,
        layerSpacing: 0.02,  // Subtle spacing between resolution layers
        rotationSpeed: 0.0005,
        autoRotate: false
    },
    
    // Camera Configuration
    camera: {
        fov: 60,
        near: 0.01,
        far: 1000,
        initialDistance: 3,
        minDistance: 0.1,  // Allow very close zoom to see individual hexagons
        maxDistance: 10
    },
    
    // Hexagon Configuration
    hexagon: {
        defaultColor: 0x4a6cf7,
        selectedColor: 0xff9800,
        hoverColor: 0x6a8cff,
        contentColor: 0x00ff88,
        borderColor: 0x6af,
        opacity: 0.85,
        borderOpacity: 0.9,
        useTextures: true,  // Whether to load hex map textures
        dataBasePath: ''  // Empty - data is symlinked into webui folder
    },
    
    // Resolution layer configuration
    // Each resolution gets its own layer at a slightly different radius
    resolutionLayers: {
        0: { radius: 1.00001, visible: true },
        1: { radius: 1.00002, visible: false },
        2: { radius: 1.00003, visible: false },
        3: { radius: 1.00004, visible: false },
        4: { radius: 1.00005, visible: false },
        5: { radius: 1.00006, visible: false },
        6: { radius: 1.00007, visible: false },
        7: { radius: 1.00008, visible: false },
        8: { radius: 1.00009, visible: false },
        9: { radius: 1.00010, visible: false },
        10: { radius: 1.00011, visible: false },
        11: { radius: 1.00012, visible: false },
        12: { radius: 1.00013, visible: false },
        13: { radius: 1.00014, visible: false },
        14: { radius: 1.00015, visible: false },
        15: { radius: 1.00016, visible: false }
    },
    
    // Lighting Configuration
    lighting: {
        ambient: {
            color: 0x404060,
            intensity: 0.4
        },
        directional: {
            color: 0xffffff,
            intensity: 1.0,
            position: { x: 5, y: 3, z: 5 }
        }
    },
    
    // Earth texture URL (using a free NASA Blue Marble texture)
    earthTexture: 'https://unpkg.com/three-globe@2.24.13/example/img/earth-blue-marble.jpg',
    
    // Fallback: simple blue sphere if texture fails to load
    earthFallbackColor: 0x1a3a5c
};

// Get mod name from URL if present
(function() {
    const urlParams = new URLSearchParams(window.location.search);
    const modName = urlParams.get('mod_name');
    if (modName) {
        CONFIG.api.modName = modName;
    }
})();
