/**
 * globe.js - 3D Globe rendering for HexGlobe
 * 
 * Manages the Three.js scene, camera, and globe with hexagon layers
 */

class HexGlobe3D {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.earth = null;
        this.hexagonLayers = {};  // Keyed by resolution
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.selectedHexagon = null;
        this.hoveredHexagon = null;
        this.onTileClick = null;  // Callback for tile clicks
        this.onTileHover = null;  // Callback for tile hover
        
        this.init();
    }
    
    /**
     * Initialize the Three.js scene
     */
    init() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a1a);
        
        // Create camera
        this.camera = new THREE.PerspectiveCamera(
            CONFIG.camera.fov,
            this.canvas.clientWidth / this.canvas.clientHeight,
            CONFIG.camera.near,
            CONFIG.camera.far
        );
        this.camera.position.z = CONFIG.camera.initialDistance;
        
        // Create renderer
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true
        });
        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        
        // Create controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = CONFIG.camera.minDistance;
        this.controls.maxDistance = CONFIG.camera.maxDistance;
        this.controls.autoRotate = CONFIG.globe.autoRotate;
        this.controls.autoRotateSpeed = 0.5;
        this.controls.zoomSpeed = 0.3;  // Slower, more granular zoom
        
        // Add lighting
        this.setupLighting();
        
        // Create Earth sphere
        this.createEarth();
        
        // Add stars background
        this.createStars();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Start animation loop
        this.animate();
    }
    
    /**
     * Setup scene lighting
     */
    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(
            CONFIG.lighting.ambient.color,
            CONFIG.lighting.ambient.intensity
        );
        this.scene.add(ambientLight);
        
        // Directional light (sun)
        const directionalLight = new THREE.DirectionalLight(
            CONFIG.lighting.directional.color,
            CONFIG.lighting.directional.intensity
        );
        directionalLight.position.set(
            CONFIG.lighting.directional.position.x,
            CONFIG.lighting.directional.position.y,
            CONFIG.lighting.directional.position.z
        );
        this.scene.add(directionalLight);
        
        // Add a subtle hemisphere light for better ambient
        const hemiLight = new THREE.HemisphereLight(0x6080a0, 0x203040, 0.3);
        this.scene.add(hemiLight);
    }
    
    /**
     * Create the Earth sphere with texture
     */
    createEarth() {
        const geometry = new THREE.SphereGeometry(
            CONFIG.globe.radius * 0.99,  // Slightly smaller than hexagon layer
            CONFIG.globe.segments,
            CONFIG.globe.segments
        );
        
        // Try to load Earth texture
        const textureLoader = new THREE.TextureLoader();
        
        textureLoader.load(
            CONFIG.earthTexture,
            (texture) => {
                // Success - create textured material
                const material = new THREE.MeshPhongMaterial({
                    map: texture,
                    bumpScale: 0.02,
                    specular: new THREE.Color(0x333333),
                    shininess: 5
                });
                
                this.earth = new THREE.Mesh(geometry, material);
                this.scene.add(this.earth);
                console.log('Earth texture loaded successfully');
            },
            undefined,
            (error) => {
                // Error - use fallback color
                console.warn('Failed to load Earth texture, using fallback color');
                const material = new THREE.MeshPhongMaterial({
                    color: CONFIG.earthFallbackColor,
                    shininess: 5
                });
                
                this.earth = new THREE.Mesh(geometry, material);
                this.scene.add(this.earth);
            }
        );
    }
    
    /**
     * Create starfield background
     */
    createStars() {
        const starsGeometry = new THREE.BufferGeometry();
        const starCount = 2000;
        const positions = new Float32Array(starCount * 3);
        
        for (let i = 0; i < starCount * 3; i += 3) {
            // Random position on a large sphere
            const radius = 50 + Math.random() * 50;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            
            positions[i] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i + 2] = radius * Math.cos(phi);
        }
        
        starsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        
        const starsMaterial = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 0.1,
            transparent: true,
            opacity: 0.8
        });
        
        const stars = new THREE.Points(starsGeometry, starsMaterial);
        this.scene.add(stars);
    }
    
    /**
     * Setup event listeners for interaction
     */
    setupEventListeners() {
        // Window resize
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Mouse events for hexagon interaction
        this.canvas.addEventListener('mousemove', (event) => this.onMouseMove(event));
        this.canvas.addEventListener('click', (event) => this.onMouseClick(event));
        this.canvas.addEventListener('dblclick', (event) => this.onMouseDoubleClick(event));
    }
    
    /**
     * Handle window resize
     */
    onWindowResize() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }
    
    /**
     * Handle mouse movement for hover effects
     */
    onMouseMove(event) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        // Raycast to find hovered hexagon
        this.raycaster.setFromCamera(this.mouse, this.camera);
        
        const hexagonMeshes = [];
        Object.values(this.hexagonLayers).forEach(layer => {
            layer.traverse((child) => {
                if (child.isMesh && child.parent?.userData?.isHexTile) {
                    hexagonMeshes.push(child);
                }
            });
        });
        
        const intersects = this.raycaster.intersectObjects(hexagonMeshes);
        
        // Reset previous hover
        if (this.hoveredHexagon && this.hoveredHexagon !== this.selectedHexagon) {
            const tileData = this.hoveredHexagon.userData.tileData;
            const color = tileData?.content ? CONFIG.hexagon.contentColor : CONFIG.hexagon.defaultColor;
            HexagonUtils.setHexagonColor(this.hoveredHexagon, color);
        }
        
        if (intersects.length > 0) {
            const hexGroup = intersects[0].object.parent;
            if (hexGroup?.userData?.isHexTile && hexGroup !== this.selectedHexagon) {
                this.hoveredHexagon = hexGroup;
                HexagonUtils.setHexagonColor(hexGroup, CONFIG.hexagon.hoverColor);
                this.canvas.style.cursor = 'pointer';
                
                if (this.onTileHover) {
                    this.onTileHover(hexGroup.userData.tileData);
                }
            }
        } else {
            this.hoveredHexagon = null;
            this.canvas.style.cursor = 'default';
            
            if (this.onTileHover) {
                this.onTileHover(null);
            }
        }
    }
    
    /**
     * Handle mouse click for selection
     */
    onMouseClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        this.raycaster.setFromCamera(this.mouse, this.camera);
        
        const hexagonMeshes = [];
        Object.values(this.hexagonLayers).forEach(layer => {
            layer.traverse((child) => {
                if (child.isMesh && child.parent?.userData?.isHexTile) {
                    hexagonMeshes.push(child);
                }
            });
        });
        
        const intersects = this.raycaster.intersectObjects(hexagonMeshes);
        
        if (intersects.length > 0) {
            const hexGroup = intersects[0].object.parent;
            if (hexGroup?.userData?.isHexTile) {
                // Deselect previous
                if (this.selectedHexagon) {
                    const prevData = this.selectedHexagon.userData.tileData;
                    const color = prevData?.content ? CONFIG.hexagon.contentColor : CONFIG.hexagon.defaultColor;
                    HexagonUtils.setHexagonColor(this.selectedHexagon, color);
                }
                
                // Select new
                this.selectedHexagon = hexGroup;
                HexagonUtils.setHexagonColor(hexGroup, CONFIG.hexagon.selectedColor);
                
                if (this.onTileClick) {
                    this.onTileClick(hexGroup.userData.tileData);
                }
            }
        }
    }
    
    /**
     * Handle mouse double-click for zoom to tile
     */
    onMouseDoubleClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        this.raycaster.setFromCamera(this.mouse, this.camera);
        
        const hexagonMeshes = [];
        Object.values(this.hexagonLayers).forEach(layer => {
            layer.traverse((child) => {
                if (child.isMesh && child.parent?.userData?.isHexTile) {
                    hexagonMeshes.push(child);
                }
            });
        });
        
        const intersects = this.raycaster.intersectObjects(hexagonMeshes);
        
        if (intersects.length > 0) {
            const hexGroup = intersects[0].object.parent;
            if (hexGroup?.userData?.isHexTile) {
                this.zoomToTile(hexGroup);
            }
        }
    }
    
    /**
     * Zoom camera to look straight down at a tile, filling ~80% of screen height
     * @param {THREE.Group} hexGroup - The hexagon group to zoom to
     */
    zoomToTile(hexGroup) {
        const tileData = hexGroup.userData.tileData;
        if (!tileData || !tileData.geometry) return;
        
        // Calculate the center of the tile
        const boundary = tileData.geometry;
        let centerLat = 0, centerLng = 0;
        boundary.forEach(([lat, lng]) => {
            centerLat += lat;
            centerLng += lng;
        });
        centerLat /= boundary.length;
        centerLng /= boundary.length;
        
        // Get the tile center as a 3D position on the globe surface
        const tileCenter = HexagonUtils.latLngToVector3(centerLat, centerLng, CONFIG.globe.radius);
        
        // Calculate the approximate width of the tile in 3D space
        // Find the maximum distance between opposite vertices
        const vertices3D = boundary.map(([lat, lng]) => 
            HexagonUtils.latLngToVector3(lat, lng, CONFIG.globe.radius)
        );
        
        let maxWidth = 0;
        for (let i = 0; i < vertices3D.length; i++) {
            for (let j = i + 1; j < vertices3D.length; j++) {
                const dist = vertices3D[i].distanceTo(vertices3D[j]);
                maxWidth = Math.max(maxWidth, dist);
            }
        }
        
        // Calculate camera distance to make tile fill ~80% of screen height
        // Using basic trigonometry: distance = (size/2) / tan(fov/2)
        const fovRad = CONFIG.camera.fov * Math.PI / 180;
        const desiredSize = maxWidth / 0.8; // Tile should be 80% of view
        const distanceFromTile = (desiredSize / 2) / Math.tan(fovRad / 2);
        
        // Camera distance from globe center (tile is on surface at radius 1.0)
        const cameraDistance = CONFIG.globe.radius + distanceFromTile;
        
        // Clamp to min/max distance
        const clampedDistance = Math.max(CONFIG.camera.minDistance, 
                                         Math.min(CONFIG.camera.maxDistance, cameraDistance));
        
        // Calculate camera position: along the normal vector from globe center through tile center
        // This ensures the camera looks perpendicular to the tile surface
        const normal = tileCenter.clone().normalize();
        const cameraPosition = normal.multiplyScalar(clampedDistance);
        
        // The look-at target should be the tile center on the globe surface
        const lookAtTarget = tileCenter.clone();
        
        // Animate camera to new position
        this.animateCameraTo(cameraPosition, lookAtTarget);
    }
    
    /**
     * Animate camera to a new position, looking at a target
     * @param {THREE.Vector3} targetPosition - Where to move the camera
     * @param {THREE.Vector3} lookAtTarget - What to look at
     */
    animateCameraTo(targetPosition, lookAtTarget) {
        const startPosition = this.camera.position.clone();
        const startTarget = this.controls.target.clone();
        
        const duration = 1000; // ms
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const t = Math.min(elapsed / duration, 1);
            
            // Ease out cubic
            const easeT = 1 - Math.pow(1 - t, 3);
            
            // Interpolate position
            this.camera.position.lerpVectors(startPosition, targetPosition, easeT);
            
            // Interpolate look-at target
            this.controls.target.lerpVectors(startTarget, lookAtTarget, easeT);
            
            this.controls.update();
            
            if (t < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    /**
     * Add hexagons for a specific resolution layer
     * @param {number} resolution - H3 resolution level
     * @param {Array} tiles - Array of tile data objects
     * @param {boolean} showAll - Whether to show all tiles or only those with content
     */
    addHexagonLayer(resolution, tiles, showAll = true) {
        // Remove existing layer if present
        if (this.hexagonLayers[resolution]) {
            this.scene.remove(this.hexagonLayers[resolution]);
        }
        
        // Create new layer group
        const layerGroup = new THREE.Group();
        layerGroup.name = `hexLayer_${resolution}`;
        
        // Calculate radius for this layer
        const layerConfig = CONFIG.resolutionLayers[resolution] || { radius: 1.0 + (resolution * CONFIG.globe.layerSpacing) };
        const radius = layerConfig.radius;
        
        console.log(`Adding hexagon layer for resolution ${resolution} at radius ${radius}`);
        console.log(`Processing ${tiles.length} tiles, showAll: ${showAll}`);
        
        let addedCount = 0;
        
        tiles.forEach(tile => {
            // Skip tiles without content if showAll is false
            if (!showAll && !tile.content) {
                return;
            }
            
            // Get geometry from tile data
            const geometry = tile.geometry;
            if (!geometry || geometry.length < 3) {
                console.warn(`Tile ${tile.id} has no valid geometry`);
                return;
            }
            
            // Create hexagon object with texture options
            const hexObject = HexagonUtils.createTileObject(tile, radius, {
                useTextures: CONFIG.hexagon.useTextures,
                dataBasePath: CONFIG.hexagon.dataBasePath
            });
            if (hexObject) {
                layerGroup.add(hexObject);
                addedCount++;
            }
        });
        
        console.log(`Added ${addedCount} hexagons to layer ${resolution}`);
        
        // Add layer to scene
        this.hexagonLayers[resolution] = layerGroup;
        this.scene.add(layerGroup);
    }
    
    /**
     * Set visibility of a resolution layer
     * @param {number} resolution - Resolution level
     * @param {boolean} visible - Whether to show the layer
     */
    setLayerVisibility(resolution, visible) {
        if (this.hexagonLayers[resolution]) {
            this.hexagonLayers[resolution].visible = visible;
        }
    }
    
    /**
     * Clear all hexagon layers
     */
    clearAllLayers() {
        Object.keys(this.hexagonLayers).forEach(resolution => {
            this.scene.remove(this.hexagonLayers[resolution]);
        });
        this.hexagonLayers = {};
    }
    
    /**
     * Animation loop
     */
    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Update controls
        this.controls.update();
        
        // Render scene
        this.renderer.render(this.scene, this.camera);
    }
    
    /**
     * Focus camera on a specific lat/lng position
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @param {number} distance - Camera distance (optional)
     */
    focusOnPosition(lat, lng, distance = null) {
        const targetPos = HexagonUtils.latLngToVector3(lat, lng, CONFIG.globe.radius);
        
        // Calculate camera position (along the same direction but further out)
        const cameraDistance = distance || this.camera.position.length();
        const cameraPos = targetPos.clone().normalize().multiplyScalar(cameraDistance);
        
        // Animate camera movement (simple version - could use GSAP for smoother animation)
        this.camera.position.copy(cameraPos);
        this.controls.target.set(0, 0, 0);
        this.controls.update();
    }
}
