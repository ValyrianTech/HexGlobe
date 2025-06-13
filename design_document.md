# HexGlobe Design Document

## 1. Project Overview

HexGlobe is a web application framework that implements a global hexagonal grid system using Uber's H3 library. It provides a platform for developers to build applications on top of a hexagonal/pentagonal tile-based world map. The framework offers a 2D representation of the world with interactive tiles that can store content and be navigated by users.

## 2. System Architecture

### 2.1 High-Level Architecture

```
+-------------------+      +-------------------+      +-------------------+
|                   |      |                   |      |                   |
|  Frontend         |      |  Backend API      |      |  Tile Storage     |
|  (HTML/JS/CSS)    +----->+  (Python/FastAPI) +----->+  (JSON Files)     |
|                   |      |                   |      |                   |
+-------------------+      +-------------------+      +-------------------+
```

### 2.2 Components

#### 2.2.1 Backend (Python/FastAPI)
- RESTful API for tile operations
- H3 integration for hexagonal grid mapping
- Tile management system
- File-based JSON storage

#### 2.2.2 Frontend
- Canvas-based hexagon visualization
- Interactive tile navigation
- Neighbor visualization and selection
- Debug information display
- Pure HTML/CSS/JavaScript implementation

## 3. Data Model

### 3.1 Class Structure

```
+----------------+
|                |
|     Tile       |
|                |
+-------+--------+
        |
        |
+-------v--------+     +----------------+
|                |     |                |
|   HexagonTile  |     |  PentagonTile  |
|                |     |                |
+----------------+     +----------------+
```

#### 3.1.1 Tile (Base Class)
- **Attributes**:
  - `id`: Unique identifier (H3 index)
  - `content`: String or JSON data stored in the tile
  - `visual_properties`: Dictionary of visual settings (border color, thickness, etc.)
  - `parent_id`: ID of the parent tile in the H3 hierarchy
  - `children_ids`: List of IDs of child tiles in the H3 hierarchy
  - `neighbor_ids`: Dictionary of neighboring tile IDs with position keys (top_left, top_middle, top_right, bottom_left, bottom_middle, bottom_right)
  - `resolution_ids`: Dictionary mapping resolution levels (0-15) to corresponding H3 indexes for the same geographic location

- **Methods**:
  - `get_neighbors()`: Returns neighboring tiles
  - `move_content_to(target_tile)`: Moves content to any tile
  - `get_parent()`: Returns the parent tile
  - `get_children()`: Returns child tiles
  - `set_visual_property(property, value)`: Sets a visual property
  - `save()`: Persists tile data to storage
  - `load()`: Loads tile data from storage
  - `_get_positioned_neighbors()`: Internal method to assign position keys to neighbors based on geographic orientation
  - `_calculate_bearing()`: Internal method to calculate bearing between points for neighbor positioning

#### 3.1.2 HexagonTile (Child Class)
- Inherits from Tile
- Specialized methods for hexagon-specific operations
- Six neighbors

#### 3.1.3 PentagonTile (Child Class)
- Inherits from Tile
- Specialized methods for pentagon-specific operations
- Five neighbors

### 3.2 Data Storage

- Tile data is split into static and dynamic components:
  - **Static data**: H3 grid information that doesn't change (parent_id, children_ids, neighbor_ids, resolution_ids)
  - **Dynamic data**: Content and visual properties that can change
- Directory structure:
  - Static data: `/data/static/res_X/aa/bb/cc/.../{tile_id}.json`
  - Dynamic data: `/data/dynamic/{mod_name}/res_X/aa/bb/cc/.../{tile_id}.json`
  - Hex map images: `/data/hex_maps/res_X/aa/bb/cc/.../{tile_id}_{timestamp}.png`
  - Where:
    - `res_X` is the H3 resolution level
    - `aa/bb/cc/...` are two-digit segments of the H3 index for efficient file organization
    - `mod_name` is the name of the mod/application (default: "default")
    - `timestamp` is an ISO 8601 formatted timestamp (with colons replaced by hyphens)
- Dynamic data files are only created when there's actual content or non-default visual properties
- Helper functions `get_static_path()`, `get_dynamic_path()`, and `get_hex_map_path()` calculate the appropriate file paths
- Hex map images use timestamp-based versioning to maintain a history of changes over time
  - Each new map generation creates a new file with the current timestamp
  - The API automatically returns the path to the most recent version
  - The frontend displays the latest map image for each tile

#### 3.2.1 Static Data JSON Structure
```json
{
  "id": "8928308280fffff",
  "parent_id": "8828308280fffff",
  "children_ids": [
    "8a28308280fffff",
    "8a28308280bffff",
    "8a28308280fffff",
    "8a28308281bffff",
    "8a28308282bffff",
    "8a28308283bffff",
    "8a28308284bffff"
  ],
  "neighbor_ids": {
    "bottom_middle": "8928308280effff",
    "bottom_left": "8928308280dffff",
    "top_left": "8928308280cffff",
    "top_middle": "8928308280bffff",
    "top_right": "8928308280affff",
    "bottom_right": "89283082809ffff"
  },
  "resolution_ids": {
    "0": "8000000000000",
    "1": "8100000000000",
    "2": "8200000000000",
    "3": "8300000000000",
    "4": "8400000000000",
    "5": "8500000000000",
    "6": "8600000000000",
    "7": "8700000000000",
    "8": "8800000000000",
    "9": "8900000000000",
    "10": "8a00000000000",
    "11": "8b00000000000",
    "12": "8c00000000000",
    "13": "8d00000000000",
    "14": "8e00000000000",
    "15": "8f00000000000"
  },
  "resolution": 9
}
```

#### 3.2.2 Dynamic Data JSON Structure
```json
{
  "id": "8928308280fffff",
  "content": "Sample content",
  "visual_properties": {
    "border_color": "#FF0000",
    "border_thickness": 2,
    "border_style": "solid",
    "fill_color": "#FFFFFF",
    "fill_opacity": 0.7
  }
}
```

## 4. API Design

### 4.1 RESTful Endpoints

#### Tile Operations
- `GET /api/tiles/{tile_id}`: Get tile information
  - Query parameter: `mod_name` (optional, default: "default")
- `PUT /api/tiles/{tile_id}`: Update tile information
  - Query parameter: `mod_name` (optional, default: "default")
- `GET /api/tiles/{tile_id}/neighbors`: Get neighboring tiles with their position information
  - Query parameter: `mod_name` (optional, default: "default")
- `GET /api/tiles/{tile_id}/parent`: Get parent tile
  - Query parameter: `mod_name` (optional, default: "default")
- `GET /api/tiles/{tile_id}/children`: Get child tiles
  - Query parameter: `mod_name` (optional, default: "default")
- `GET /api/tiles/{tile_id}/resolutions`: Get resolution IDs for the tile
  - Query parameter: `mod_name` (optional, default: "default")
- `POST /api/tiles/{tile_id}/move-content/{target_id}`: Move content to target tile
  - Query parameter: `mod_name` (optional, default: "default")
- `GET /api/tiles/{tile_id}/grid`: Get a 2D grid of H3 indexes centered around the specified tile
  - Query parameter: `mod_name` (optional, default: "default")

#### Geocoding Operations
- `GET /api/geocode/`: Convert an address or coordinates to an H3 index
  - Query parameters:
    - `address` (optional): String containing the address to geocode
    - `lat` (optional): Latitude coordinate
    - `lng` (optional): Longitude coordinate
    - `resolution` (optional, default: 9): H3 resolution level
  - Returns: H3 index, coordinates, and address information

#### Visual Operations
- `PUT /api/tiles/{tile_id}/visual`: Update visual properties
  - Query parameter: `mod_name` (optional, default: "default")

### 4.2 WebSocket Endpoints (Future Enhancement)
- `/ws/tiles/{tile_id}`: Real-time updates for tile changes

## 5. Frontend Design

### 5.1 UI Components

- **Main View**: Displays the active tile and its immediate neighbors
- **HexTile Component**: Canvas-based hexagon rendering with grid pattern and tile info
- **Navigation Controls**: Allows users to navigate between tiles and change resolution levels
- **Zoom Control**: Slider to adjust the zoom level (1-10), controlling how many hex tiles are visible
  - Zoom level 1: Shows only the active tile (taking up 80% of the canvas)
  - Zoom level 2: Shows the active tile plus 1 ring of neighbors (3 hexagons in diameter)
  - Zoom level 3: Shows the active tile plus 2 rings of neighbors (5 hexagons in diameter)
  - And so on for higher zoom levels
- **Resolution Control**: Slider to adjust the H3 resolution (0-15), controlling the size of hexagons on Earth's surface

### 5.2 Hexagon Rendering Specifications

#### 5.2.1 Hexagon Geometry

The standard hexagon used in HexGlobe is rendered in a 1024x1024 pixel canvas with the following specifications:

- **Orientation**: Flat-bottom hexagon
- **Center Point**: (512.0, 512.0)
- **Radius**: 512.0 pixels (distance from center to any vertex)

The six vertices of the hexagon are positioned at the following coordinates (clockwise from the rightmost point):

1. Vertex 1 (angle 0°): (1024.0, 512.0) - right middle
2. Vertex 2 (angle 60°): (768.0, 955.4) - bottom right
3. Vertex 3 (angle 120°): (256.0, 955.4) - bottom left
4. Vertex 4 (angle 180°): (0.0, 512.0) - left middle
5. Vertex 5 (angle 240°): (256.0, 68.6) - top left
6. Vertex 6 (angle 300°): (768.0, 68.6) - top right

This geometry ensures that:
- The hexagon extends to the full edges of the image on the left and right sides
- The hexagon is perfectly centered in the canvas
- The flat-bottom orientation aligns with the H3 grid system's representation

### 5.2.2 Hexagon Map Image Generation

HexGlobe includes a map image generation script (`frontend/assets/generate_hex_map.py`) that creates precisely calibrated hexagonal map images for each H3 tile. These images are used as the background for hexagon tiles in the frontend visualization. The image generation process includes:

- **Map Rendering**: Uses StaticMap to render OpenStreetMap data for the geographic area of each H3 hexagon
- **Rotation and Alignment**: Rotates the map to align with flat-bottom hexagon orientation
- **Vertical Scaling**: Applies a vertical scaling transformation to correct for projection distortion
- **Horizontal Skew**: Applies a horizontal skew transformation to further improve vertex alignment
- **Calibration Aids**: Draws three concentric hexagons (main green border, inner blue border, outer red border)
- **Reference Dots**: Places black reference dots at the six vertices of a perfect hexagon for alignment verification
- **Debug Options**: Supports debug mode for displaying intermediate images and vertex coordinates
- **Timestamp Versioning**: Each generated map is saved with a timestamp to maintain a history of changes

The generated images are stored in the backend directory structure under `data/hex_maps/res_<resolution>/...` with timestamps in the filenames, and are accessed by the frontend via relative paths. The frontend clips these images to hexagonal shapes when rendering.

The map generation process ensures that:
- Hexagon vertices align perfectly with the frontend's hexagon rendering
- Adjacent hexagon tiles have seamless boundaries
- The visual representation matches the mathematical H3 hexagon boundaries
- Calibration aids assist in verifying proper alignment
- Historical versions of maps are preserved with timestamp-based filenames

### 5.3 Interaction Flow

1. User loads the application, which displays the default active tile
2. Neighboring tiles are visible around the active tile
3. User can adjust the zoom level to see more or fewer tiles
4. User can adjust the resolution to change the size of hexagons on Earth's surface
5. User clicks on a tile to select it
   - Clicking a selected tile unselects it
   - Multiple tiles can be selected simultaneously
   - Selected tiles are visually highlighted with distinct styling
   - The most recently selected tile becomes the "focus" tile with a special visual style
   - When a tile is unselected, focus shifts to the last selected tile (if any)
6. When exactly one tile is selected, a navigation button appears
7. Clicking the navigation button makes the selected tile the active tile
8. The view updates to show the new active tile and its neighbors

### 5.4 Visualization Approach

#### Current Implementation
- Pure Canvas-based hexagon rendering
- Grid pattern inside hexagons to simulate map data
- Tile information panel showing active tile details
- Multi-selection of tiles with toggle behavior
- Focus tile tracking (last selected tile) with distinct visual styling
- Selected tiles list in the debug panel
- Conditional navigation button when exactly one tile is selected
- Zoom control to adjust visible hex tiles
- Resolution control to adjust hexagon size on Earth's surface
- Neighbor visualization with click navigation
- Flat-bottom hexagon orientation with proper alignment between tiles
- Consistent coordinate system using (row, col) format

#### Future Map Integration
- Each hexagon will be filled with corresponding map data
- Custom rendering of map features within hexagon boundaries
- Potential for different map styles or data sources per hexagon

### 5.5 JavaScript Implementation

- **Structure**:
  - `index.html`: Main HTML entry point
  - `css/styles.css`: Main stylesheet
  - `js/app.js`: Main application logic
  - `js/hexTile.js`: Canvas-based hexagon rendering module
  - `js/navigation.js`: Controls for navigating between tiles

- **State Management**:
  - Vanilla JavaScript for managing application state
  - Custom event system for handling UI updates
  - LocalStorage for persisting state between sessions

- **H3 Integration**:
  - Removed from frontend, now handled by backend API

## 6. Implementation Progress

### 6.1 Completed
- Set up FastAPI backend with CORS configuration
- Implemented Tile model with H3 integration
- Created basic API endpoints for tile operations
- Developed Canvas-based hexagon visualization
- Implemented neighbor visualization
- Added zoom control slider (1-10) for adjusting visible hex tiles
- Added resolution control slider (0-15) for adjusting hexagon size on Earth's surface
- Set up GitHub repository and version control
- Implemented frontend-backend integration with API calls
- Added comprehensive logging to backend API endpoints
- Fixed tile data persistence with proper JSON serialization
- Implemented click navigation between hexagons
- Added grid endpoint to return a 2D grid of H3 indexes centered around a specified tile
- Updated frontend to use the grid endpoint for accurate hexagon positioning
- Added neighbor_ids to tile data, ordered in a consistent clockwise manner
- Added resolution_ids to tile data, mapping resolution levels to corresponding H3 indexes
- Added API endpoint for retrieving resolution IDs for a tile
- Fixed hexagon positioning to correctly display neighbor tiles in proper grid alignment
- Corrected coordinate system to consistently use (row, col) format
- Implemented flat-bottom hexagon orientation with proper vertex calculation
- Added proper vertical offset for odd columns to maintain hexagonal grid alignment
- Created hexagon map image generation script with precise calibration features
- Implemented vertical scaling and horizontal skew transformations for accurate hexagon alignment
- Added calibration aids (concentric hexagons and reference dots) to map images
- Ensured seamless boundaries between adjacent hexagon tiles
- Implemented multi-selection functionality for hexagon tiles
- Added visual styling for selected tiles with orange border and yellow fill
- Added selected tiles list to the debug panel
- Implemented conditional navigation button when exactly one tile is selected
- Implemented timestamp-based versioning system for hex map images
- Added automatic retrieval of the latest map version for each tile
- Implemented unrestricted tile content movement between any tiles regardless of proximity
- Added "Go To" navigation feature with H3 index and address input support
- Implemented address-to-H3 conversion using Nominatim/OpenStreetMap
- Implemented pentagon grid rendering solution for handling irregular topology at low resolutions

### 6.2 Pentagon Grid Rendering

HexGlobe uses the H3 library which creates a global hexagonal grid with 12 pentagons at resolution 0. These pentagons create topological irregularities that need special handling:

#### 6.2.1 Problem

- Pentagons have 5 neighbors instead of 6, creating coordinate conflicts in a regular grid layout
- The original neighbor-based grid placement algorithm assumes a regular hexagonal grid
- When pentagons are present, the algorithm fails to place all tiles correctly

#### 6.2.2 Solution

HexGlobe implements a dual-algorithm approach for grid generation:

1. **Regular Hexagonal Grid Algorithm**:
   - Used when no pentagons are present in the grid
   - Places tiles based on neighbor relationships and relative grid coordinates
   - Maintains a regular hexagonal grid structure

2. **Geographic Coordinate-Based Algorithm**:
   - Automatically activated when pentagons are detected in the grid
   - Groups tiles by latitude into buckets (rows) based on the square root of total tiles
   - Sorts tiles within each row by longitude (west to east)
   - Assigns grid coordinates relative to the center tile's position
   - Ensures the center tile is always at (0,0) in the grid

This approach preserves the spherical topology of the H3 grid while providing a consistent 2D representation that can be rendered by the frontend without modification.

### 6.3 In Progress
- Enhancing frontend to utilize the ordered neighbor_ids for more intuitive navigation
- Implementing UI for displaying and navigating between different resolution levels

### 6.4 Future Enhancements
- WebSocket integration for real-time updates
- Map data integration within hexagons
- User authentication and authorization
- Custom content editors for tiles
- Mobile-responsive design
- Performance optimizations for large grids
- Advanced visualization options

## 7. Mod Support

### 7.1 Overview

HexGlobe supports multiple mods or applications using the same underlying hexagonal grid structure. This allows different applications to share the same static H3 grid data while maintaining separate dynamic content and visual properties.

### 7.2 Implementation

- **Mod Name Parameter**: All API endpoints accept an optional `mod_name` parameter (default: "default")
- **Data Storage**:
  - Static data (H3 grid information) is shared across all mods
  - Dynamic data (content and visual properties) is stored separately for each mod
  - Directory structure: `/data/dynamic/{mod_name}/res_X/aa/bb/cc/.../{tile_id}.json`
- **Storage Optimization**:
  - Dynamic data files are only created when there's actual content or non-default visual properties
  - Empty or default tiles don't create dynamic data files, improving storage efficiency
  - When a tile's content and visual properties are reset to defaults, the dynamic file is removed

### 7.3 Frontend Mod System

#### 7.3.1 ModLoader

The frontend includes a ModLoader system that dynamically loads mods based on URL parameters:

- **ModLoader.js**: Core module responsible for loading mod assets
  - Parses URL parameters to determine which mod to load (`?mod_name=mod_name`)
  - Loads the mod's manifest.json file
  - Dynamically loads CSS and JavaScript files specified in the manifest
  - Falls back to the default mod if loading fails
  - Dispatches a `modLoaded` event when initialization is complete
  - Provides utility methods for constructing API URLs with the mod_name parameter

#### 7.3.2 Mod Structure

Each mod follows a standard directory structure:

```
mods/
├── default/             # Default mod (fallback)
│   ├── manifest.json    # Mod metadata and configuration
│   ├── css/
│   │   └── theme.css    # Theme CSS that can be customized
│   ├── js/
│   │   └── mod.js       # Mod logic and event handlers
│   └── README.md        # Documentation
└── custom_mod/          # Custom mod example
    ├── manifest.json
    ├── css/
    │   └── theme.css
    ├── js/
    │   └── mod.js
    └── README.md
```

#### 7.3.3 Manifest Format

Each mod must include a manifest.json file with the following structure:

```json
{
  "name": "Mod Name",
  "version": "1.0.0",
  "description": "Description of the mod",
  "author": "Author Name",
  "theme": "css/theme.css",
  "script": "js/mod.js"
}
```

#### 7.3.4 API Integration

- All API calls include the mod_name parameter to ensure data separation
- The ModLoader provides a `getModName()` method to retrieve the current mod name
- The navigation.js module uses this method to construct API URLs with the correct mod_name parameter

#### 7.3.5 Event System

The mod system uses a custom event system to notify the application when a mod is loaded:

- `modLoaded`: Dispatched when a mod is successfully loaded, includes mod name and manifest
- Mod JavaScript files listen for this event to initialize themselves

### 7.4 Benefits

- **Resource Efficiency**: Static H3 grid data is shared, reducing storage requirements
- **Separation of Concerns**: Different applications can use the same grid without interfering with each other
- **Storage Optimization**: Only tiles with actual content create files, minimizing disk usage
- **Scalability**: The system can support many different mods without duplicating the underlying grid structure
- **Dynamic Loading**: Mods can be loaded at runtime without requiring application restart
- **Fallback Mechanism**: If a mod fails to load, the system falls back to the default mod
- **Customization**: Mods can customize both visual appearance and behavior
- **Isolation**: Each mod's data is isolated from other mods

## 8. Technology Stack

- **Backend**: Python 3.12, FastAPI, H3 Python bindings
- **Frontend**: HTML5, CSS3, JavaScript, Canvas API
- **Data Storage**: File-based JSON
- **Development Tools**: Git, Poetry (dependency management)

## 9. Extension Points

- **Custom Content Types**: Extend the content model to support different types of data
- **Alternative Map Providers**: Add support for different map data sources
- **Game Rules**: Implement specific game mechanics on top of the framework
- **Data Visualization**: Add support for visualizing data within tiles
- **Mobile Support**: Optimize the UI for mobile devices
- **Offline Mode**: Implement local storage for offline usage
- **Multi-User Support**: Add authentication and user-specific views
