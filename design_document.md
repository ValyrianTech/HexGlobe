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
  - `move_content_to(target_tile)`: Moves content to a neighboring tile
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

- Each tile's data stored as a separate JSON file
- Filename format: `{tile_id}.json`
- Directory structure: `/data/tiles/`
- Sample JSON structure:
```json
{
  "id": "8928308280fffff",
  "content": "Sample content",
  "visual_properties": {
    "border_color": "#FF0000",
    "border_thickness": 2,
    "border_style": "solid",
    "fill_color": "#FFFFFF"
  },
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
  }
}
```

## 4. API Design

### 4.1 RESTful Endpoints

#### Tile Operations
- `GET /api/tiles/{tile_id}`: Get tile information
- `PUT /api/tiles/{tile_id}`: Update tile information
- `GET /api/tiles/{tile_id}/neighbors`: Get neighboring tiles with their position information
- `GET /api/tiles/{tile_id}/parent`: Get parent tile
- `GET /api/tiles/{tile_id}/children`: Get child tiles
- `GET /api/tiles/{tile_id}/resolutions`: Get resolution IDs for the tile
- `POST /api/tiles/{tile_id}/move-content/{target_id}`: Move content to target tile
- `GET /api/tiles/{tile_id}/grid`: Get a 2D grid of H3 indexes centered around the specified tile

#### Visual Operations
- `PUT /api/tiles/{tile_id}/visual`: Update visual properties

### 4.2 WebSocket Endpoints (Future Enhancement)
- `/ws/tiles/{tile_id}`: Real-time updates for tile changes

## 5. Frontend Design

### 5.1 UI Components

- **Main View**: Displays the active tile and its immediate neighbors
- **HexTile Component**: Canvas-based hexagon rendering with grid pattern and tile info
- **Navigation Controls**: Allows users to navigate between tiles and change resolution levels
- **Zoom Control**: Slider to adjust the zoom level (1-10), controlling how many hex tiles are visible
- **Resolution Control**: Slider to adjust the H3 resolution (0-15), controlling the size of hexagons on Earth's surface

### 5.2 Interaction Flow

1. User loads the application, which displays the default active tile
2. Neighboring tiles are visible around the active tile
3. User can adjust the zoom level to see more or fewer tiles
4. User can adjust the resolution to change the size of hexagons on Earth's surface
5. User clicks on a neighboring tile
6. The clicked tile becomes the active tile with a smooth transition
7. The view updates to show the new active tile and its neighbors

### 5.3 Visualization Approach

#### Current Implementation
- Pure Canvas-based hexagon rendering
- Grid pattern inside hexagons to simulate map data
- Tile information panel showing active tile details
- Zoom control to adjust visible hex tiles
- Resolution control to adjust hexagon size on Earth's surface
- Neighbor visualization with click navigation
- Flat-bottom hexagon orientation with proper alignment between tiles
- Consistent coordinate system using (row, col) format

#### Future Map Integration
- Each hexagon will be filled with corresponding map data
- Custom rendering of map features within hexagon boundaries
- Potential for different map styles or data sources per hexagon

### 5.4 JavaScript Implementation

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
  - h3-js library used for frontend hexagonal grid calculations
  - Neighbor calculation and resolution management
  - Coordinate conversion for proper hexagon rendering
  - Resolution conversion for adjusting hexagon size

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

### 6.2 In Progress
- Enhancing frontend to utilize the ordered neighbor_ids for more intuitive navigation
- Implementing UI for displaying and navigating between different resolution levels

### 6.3 Future Enhancements
- WebSocket integration for real-time updates
- Map data integration within hexagons
- User authentication and authorization
- Custom content editors for tiles
- Mobile-responsive design
- Performance optimizations for large grids
- Advanced visualization options

## 7. Technology Stack

- **Backend**: Python 3.12, FastAPI, H3 Python bindings
- **Frontend**: HTML5, CSS3, JavaScript, Canvas API, h3-js
- **Data Storage**: File-based JSON
- **Development Tools**: Git, Poetry (dependency management)

## 8. Extension Points

- **Custom Content Types**: Extend the content model to support different types of data
- **Alternative Map Providers**: Add support for different map data sources
- **Game Rules**: Implement specific game mechanics on top of the framework
- **Data Visualization**: Add support for visualizing data within tiles
- **Mobile Support**: Optimize the UI for mobile devices
- **Offline Mode**: Implement local storage for offline usage
- **Multi-User Support**: Add authentication and user-specific views
