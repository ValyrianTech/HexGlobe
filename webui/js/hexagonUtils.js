/**
 * hexagonUtils.js - Utilities for creating hexagon geometries on a sphere
 * 
 * Converts H3 hexagon boundaries to Three.js geometries positioned on a sphere
 */

// Texture loader and cache
const textureLoader = new THREE.TextureLoader();
const textureCache = {};

const HexagonUtils = {
    /**
     * Convert lat/lng to 3D position on a sphere
     * @param {number} lat - Latitude in degrees
     * @param {number} lng - Longitude in degrees
     * @param {number} radius - Sphere radius
     * @returns {THREE.Vector3} - 3D position
     */
    latLngToVector3(lat, lng, radius) {
        const phi = (90 - lat) * (Math.PI / 180);
        const theta = (lng + 180) * (Math.PI / 180);
        
        const x = -radius * Math.sin(phi) * Math.cos(theta);
        const y = radius * Math.cos(phi);
        const z = radius * Math.sin(phi) * Math.sin(theta);
        
        return new THREE.Vector3(x, y, z);
    },
    
    /**
     * Find the index of the bottom edge (closest to equator) in the boundary
     * @param {Array} boundary - Array of [lat, lng] coordinates
     * @returns {number} - Index of the first vertex of the bottom edge
     */
    findBottomEdgeIndex(boundary) {
        let minLatDiff = Infinity;
        let bottomEdgeIdx = 0;
        
        for (let i = 0; i < boundary.length; i++) {
            const nextI = (i + 1) % boundary.length;
            // Average latitude of the edge (midpoint)
            const edgeLat = (boundary[i][0] + boundary[nextI][0]) / 2;
            const latDiff = Math.abs(edgeLat); // Distance from equator
            
            if (latDiff < minLatDiff) {
                minLatDiff = latDiff;
                bottomEdgeIdx = i;
            }
        }
        
        return bottomEdgeIdx;
    },
    
    /**
     * Reorder boundary vertices to match hex map image orientation
     * The hex map images have vertices ordered: right-middle, bottom-right, bottom-left, left-middle, top-left, top-right
     * @param {Array} boundary - Array of [lat, lng] coordinates
     * @returns {Array} - Reordered boundary with bottom edge at indices 1-2
     */
    reorderBoundaryForTexture(boundary) {
        const numVertices = boundary.length;
        
        // Find the bottom edge (closest to equator)
        const bottomEdgeIdx = this.findBottomEdgeIndex(boundary);
        
        // The bottom edge goes from vertex[bottomEdgeIdx] to vertex[bottomEdgeIdx+1]
        // In the texture, the order is: right-middle(0), bottom-right(1), bottom-left(2), left-middle(3), top-left(4), top-right(5)
        // The bottom edge in texture is between indices 1 and 2
        
        // H3 boundaries are counter-clockwise when viewed from above
        // We need to determine which vertex of the bottom edge is on the right (bottom-right)
        
        const v1 = boundary[bottomEdgeIdx];
        const v2 = boundary[(bottomEdgeIdx + 1) % numVertices];
        
        // Compare longitudes to determine which is on the right
        // The one with larger longitude is on the right (east)
        let bottomRightIdx, bottomLeftIdx;
        if (v1[1] > v2[1]) {
            // v1 is to the right
            bottomRightIdx = bottomEdgeIdx;
            bottomLeftIdx = (bottomEdgeIdx + 1) % numVertices;
        } else {
            // v2 is to the right
            bottomRightIdx = (bottomEdgeIdx + 1) % numVertices;
            bottomLeftIdx = bottomEdgeIdx;
        }
        
        // Now we need to build the array starting from right-middle
        // Going clockwise from right-middle: right-middle -> bottom-right -> bottom-left -> left-middle -> top-left -> top-right
        // right-middle is one step before bottom-right in clockwise direction
        // Since H3 is counter-clockwise, one step before in clockwise = one step forward in H3 order
        const rightMiddleIdx = (bottomRightIdx + 1) % numVertices;
        
        // Build reordered array going clockwise (which is backwards in H3's counter-clockwise order)
        const reordered = [];
        for (let i = 0; i < numVertices; i++) {
            const idx = (rightMiddleIdx - i + numVertices) % numVertices;
            reordered.push(boundary[idx]);
        }
        
        return reordered;
    },
    
    /**
     * Create a hexagon/pentagon mesh from tile boundary coordinates
     * @param {Array} boundary - Array of [lat, lng] coordinates
     * @param {number} radius - Sphere radius for this layer
     * @param {number} color - Hex color
     * @param {number} opacity - Opacity (0-1)
     * @param {boolean} useTextureUVs - Whether to use texture-oriented UV mapping
     * @returns {THREE.Mesh} - The hexagon mesh
     */
    createHexagonMesh(boundary, radius, color = 0x4a6cf7, opacity = 0.7, useTextureUVs = false) {
        if (!boundary || boundary.length < 3) {
            console.warn('Invalid boundary for hexagon');
            return null;
        }
        
        // Reorder boundary to match hex map texture orientation if using textures
        const orderedBoundary = useTextureUVs ? this.reorderBoundaryForTexture(boundary) : boundary;
        
        // Convert boundary points to 3D vectors
        const points = orderedBoundary.map(([lat, lng]) => 
            this.latLngToVector3(lat, lng, radius)
        );
        
        // Calculate center point (average of all vertices)
        const center = new THREE.Vector3();
        points.forEach(p => center.add(p));
        center.divideScalar(points.length);
        
        // Place center slightly below the sphere surface so the flat triangular faces
        // sit closer to the sphere surface rather than floating above it
        center.normalize().multiplyScalar(radius * 0.999);
        
        // Create geometry using triangles from center to each edge
        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        const uvs = [];
        const indices = [];
        
        // Add center vertex (UV at center of texture)
        vertices.push(center.x, center.y, center.z);
        uvs.push(0.5, 0.5);
        
        // Add boundary vertices with UV coordinates
        // For a flat-bottom hexagon texture, the UV positions are:
        // Vertex 0 (right-middle): u=1.0, v=0.5
        // Vertex 1 (bottom-right): u=0.75, v=0.933 (sin(60°)*0.5 + 0.5)
        // Vertex 2 (bottom-left): u=0.25, v=0.933
        // Vertex 3 (left-middle): u=0.0, v=0.5
        // Vertex 4 (top-left): u=0.25, v=0.067
        // Vertex 5 (top-right): u=0.75, v=0.067
        
        const numPoints = points.length;
        // UV coordinates flipped vertically (1-v) to correct mirroring
        // In Three.js, V=0 is bottom, V=1 is top, but images have Y=0 at top
        const hexUVs = [
            [1.0, 0.5],    // right-middle
            [0.75, 0.067], // bottom-right (was 0.933)
            [0.25, 0.067], // bottom-left (was 0.933)
            [0.0, 0.5],    // left-middle
            [0.25, 0.933], // top-left (was 0.067)
            [0.75, 0.933]  // top-right (was 0.067)
        ];
        
        // Pentagon UVs (5 vertices) - also flipped
        const pentUVs = [
            [1.0, 0.5],    // right
            [0.65, 0.05],  // bottom-right (was 0.95)
            [0.15, 0.25],  // bottom-left (was 0.75)
            [0.15, 0.75],  // top-left (was 0.25)
            [0.65, 0.95]   // top-right (was 0.05)
        ];
        
        const uvTemplate = numPoints === 6 ? hexUVs : pentUVs;
        
        points.forEach((p, i) => {
            vertices.push(p.x, p.y, p.z);
            
            if (useTextureUVs && i < uvTemplate.length) {
                // Use predefined UV coordinates for textured hexagons
                uvs.push(uvTemplate[i][0], uvTemplate[i][1]);
            } else {
                // Fallback: circular UV pattern for non-textured hexagons
                const angle = (i / numPoints) * Math.PI * 2 - Math.PI / 2;
                const uvRadius = 0.5;
                const u = 0.5 + uvRadius * Math.cos(angle);
                const v = 0.5 + uvRadius * Math.sin(angle);
                uvs.push(u, v);
            }
        });
        
        // Create triangles (fan from center)
        for (let i = 0; i < points.length; i++) {
            const next = (i + 1) % points.length;
            indices.push(0, i + 1, next + 1);
        }
        
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
        geometry.setIndex(indices);
        geometry.computeVertexNormals();
        
        // Create material - always start with color, texture will be applied later
        const material = new THREE.MeshPhongMaterial({
            color: color,
            transparent: true,
            opacity: opacity,
            side: THREE.DoubleSide,
            shininess: 30,
            depthWrite: true,
            polygonOffset: true,
            polygonOffsetFactor: 0,
            polygonOffsetUnits: 0
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.renderOrder = 0;  // Ensure consistent render order
        return mesh;
    },
    
    /**
     * Load a texture for a tile
     * @param {string} texturePath - Path to the texture image
     * @param {Function} onLoad - Callback when texture is loaded
     * @returns {THREE.Texture|null} - The texture or null if not available
     */
    loadTexture(texturePath, onLoad = null) {
        if (!texturePath) return null;
        
        // Check cache first
        if (textureCache[texturePath]) {
            if (onLoad) onLoad(textureCache[texturePath]);
            return textureCache[texturePath];
        }
        
        // Load texture
        const texture = textureLoader.load(
            texturePath,
            (loadedTexture) => {
                textureCache[texturePath] = loadedTexture;
                console.log(`Texture loaded: ${texturePath}`);
                if (onLoad) onLoad(loadedTexture);
            },
            undefined,
            (error) => {
                console.warn(`Failed to load texture: ${texturePath}`);
            }
        );
        
        return texture;
    },
    
    /**
     * Create a hexagon border (outline) from tile boundary coordinates
     * @param {Array} boundary - Array of [lat, lng] coordinates
     * @param {number} radius - Sphere radius for this layer
     * @param {number} color - Hex color
     * @returns {THREE.Line} - The border line
     */
    createHexagonBorder(boundary, radius, color = 0x6af) {
        if (!boundary || boundary.length < 3) {
            return null;
        }
        
        // Convert boundary points to 3D vectors
        const points = boundary.map(([lat, lng]) => 
            this.latLngToVector3(lat, lng, radius * 1.0001) // Very slightly larger to avoid z-fighting
        );
        
        // Close the loop
        points.push(points[0].clone());
        
        // Create geometry
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        
        // Create material
        const material = new THREE.LineBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.9
        });
        
        return new THREE.Line(geometry, material);
    },
    
    /**
     * Create a complete hexagon tile (mesh + border) with metadata
     * @param {Object} tileData - Tile data from API
     * @param {number} radius - Sphere radius
     * @param {Object} options - Rendering options
     * @returns {THREE.Group} - Group containing mesh and border
     */
    createTileObject(tileData, radius, options = {}) {
        const {
            color = CONFIG.hexagon.defaultColor,
            opacity = CONFIG.hexagon.opacity,
            borderColor = CONFIG.hexagon.borderColor,
            showBorder = true,
            useTextures = true,
            dataBasePath = '../frontend'
        } = options;
        
        // Get boundary from tile geometry or calculate from H3
        // The API returns geometry as [[lat, lng], ...]
        const boundary = tileData.geometry || this.estimateBoundary(tileData);
        
        if (!boundary) {
            console.warn(`No boundary for tile ${tileData.id}`);
            return null;
        }
        
        const group = new THREE.Group();
        group.userData = {
            tileId: tileData.id,
            tileData: tileData,
            isHexTile: true
        };
        
        // Determine color based on content
        let tileColor = color;
        if (tileData.content) {
            tileColor = CONFIG.hexagon.contentColor;
        }
        
        // Check if we should load a texture
        const hasTexture = useTextures && tileData.latest_map;
        
        // Create mesh with proper UV mapping based on whether texture will be used
        // Pass a placeholder truthy value if texture will be loaded to trigger proper UV mapping
        const mesh = this.createHexagonMesh(boundary, radius, tileColor, opacity, hasTexture ? true : null);
        
        if (hasTexture) {
            // Construct the full path to the texture
            const texturePath = `${dataBasePath}/${tileData.latest_map}`;
            
            // Load texture asynchronously and update mesh when ready
            this.loadTexture(texturePath, (loadedTexture) => {
                // Find the mesh in the group and update its material
                group.traverse((child) => {
                    if (child.isMesh && child.userData.tileId === tileData.id) {
                        child.material.map = loadedTexture;
                        child.material.color.setHex(0xffffff); // Reset color to white for texture
                        child.material.needsUpdate = true;
                    }
                });
            });
        }
        if (mesh) {
            mesh.userData = { tileId: tileData.id };
            group.add(mesh);
        }
        
        // Create border
        if (showBorder) {
            const border = this.createHexagonBorder(boundary, radius, borderColor);
            if (border) {
                group.add(border);
            }
        }
        
        return group;
    },
    
    /**
     * Estimate boundary for a tile if geometry is not provided
     * This creates a rough hexagon at the tile's center
     * @param {Object} tileData - Tile data
     * @returns {Array} - Estimated boundary coordinates
     */
    estimateBoundary(tileData) {
        // If we have neighbor_ids, we can estimate the center
        // For now, return null and rely on API providing geometry
        return null;
    },
    
    /**
     * Update hexagon color (for hover/selection effects)
     * @param {THREE.Group} hexGroup - The hexagon group
     * @param {number} color - New color
     */
    setHexagonColor(hexGroup, color) {
        hexGroup.traverse((child) => {
            if (child.isMesh && child.material) {
                child.material.color.setHex(color);
            }
        });
    },
    
    /**
     * Update hexagon opacity
     * @param {THREE.Group} hexGroup - The hexagon group
     * @param {number} opacity - New opacity (0-1)
     */
    setHexagonOpacity(hexGroup, opacity) {
        hexGroup.traverse((child) => {
            if (child.isMesh && child.material) {
                child.material.opacity = opacity;
            }
        });
    }
};
