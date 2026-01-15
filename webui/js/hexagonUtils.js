/**
 * hexagonUtils.js - Utilities for creating hexagon geometries on a sphere
 * 
 * Converts H3 hexagon boundaries to Three.js geometries positioned on a sphere
 */

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
     * Create a hexagon/pentagon mesh from tile boundary coordinates
     * @param {Array} boundary - Array of [lat, lng] coordinates
     * @param {number} radius - Sphere radius for this layer
     * @param {number} color - Hex color
     * @param {number} opacity - Opacity (0-1)
     * @returns {THREE.Mesh} - The hexagon mesh
     */
    createHexagonMesh(boundary, radius, color = 0x4a6cf7, opacity = 0.7) {
        if (!boundary || boundary.length < 3) {
            console.warn('Invalid boundary for hexagon');
            return null;
        }
        
        // Convert boundary points to 3D vectors
        const points = boundary.map(([lat, lng]) => 
            this.latLngToVector3(lat, lng, radius)
        );
        
        // Calculate center point (average of all vertices)
        const center = new THREE.Vector3();
        points.forEach(p => center.add(p));
        center.divideScalar(points.length);
        
        // Normalize center to be on the sphere surface
        center.normalize().multiplyScalar(radius);
        
        // Create geometry using triangles from center to each edge
        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        const indices = [];
        
        // Add center vertex
        vertices.push(center.x, center.y, center.z);
        
        // Add boundary vertices
        points.forEach(p => {
            vertices.push(p.x, p.y, p.z);
        });
        
        // Create triangles (fan from center)
        for (let i = 0; i < points.length; i++) {
            const next = (i + 1) % points.length;
            indices.push(0, i + 1, next + 1);
        }
        
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setIndex(indices);
        geometry.computeVertexNormals();
        
        // Create material
        const material = new THREE.MeshPhongMaterial({
            color: color,
            transparent: true,
            opacity: opacity,
            side: THREE.DoubleSide,
            shininess: 30
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        return mesh;
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
            this.latLngToVector3(lat, lng, radius * 1.001) // Slightly larger to avoid z-fighting
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
            showBorder = true
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
        
        // Create mesh
        const mesh = this.createHexagonMesh(boundary, radius, tileColor, opacity);
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
