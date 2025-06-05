# HexGlobe Design Document

## 1. Project Overview

HexGlobe is a web application framework that implements a global hexagonal grid system using Uber's H3 library. It provides a platform for developers to build applications on top of a hexagonal/pentagonal tile-based world map. The framework offers a 2D representation of the world with interactive tiles that can store content and be navigated by users.

## 2. System Architecture

### 2.1 High-Level Architecture

```
+-------------------+      +-------------------+      +-------------------+
|                   |      |                   |      |                   |
|  Frontend         |      |  Backend API      |      |  Tile Storage     |
|  (HTML/CSS/JS)    +----->+  (Python/FastAPI) +----->+  (JSON Files)     |
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
- Interactive tile visualization
- OpenStreetMap integration
- UI for tile navigation and interaction

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

- **Methods**:
  - `get_neighbors()`: Returns neighboring tiles
  - `move_content_to(target_tile)`: Moves content to a neighboring tile
  - `get_parent()`: Returns the parent tile
  - `get_children()`: Returns child tiles
  - `set_visual_property(property, value)`: Sets a visual property
  - `save()`: Persists tile data to storage
  - `load()`: Loads tile data from storage

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
  ]
}
```

## 4. API Design

### 4.1 RESTful Endpoints

#### Tile Operations
- `GET /api/tiles/{tile_id}`: Get tile information
- `PUT /api/tiles/{tile_id}`: Update tile information
- `GET /api/tiles/{tile_id}/neighbors`: Get neighboring tiles
- `GET /api/tiles/{tile_id}/parent`: Get parent tile
- `GET /api/tiles/{tile_id}/children`: Get child tiles
- `POST /api/tiles/{tile_id}/move-content/{target_id}`: Move content to target tile

#### Visual Operations
- `PUT /api/tiles/{tile_id}/visual`: Update visual properties

### 4.2 WebSocket Endpoints (Future Enhancement)
- `/ws/tiles/{tile_id}`: Real-time updates for tile changes

## 5. Frontend Design

### 5.1 UI Components

- **Main View**: Displays the active tile and its immediate neighbors
- **Tile Component**: Renders individual tiles with their content and visual properties
- **Navigation Controls**: Allows users to navigate between tiles and change resolution levels

### 5.2 Interaction Flow

1. User loads the application, which displays the default active tile
2. Neighboring tiles are partially visible around the active tile
3. User clicks on a neighboring tile
4. The clicked tile becomes the active tile with a smooth transition
5. The view updates to show the new active tile and its neighbors

### 5.3 OpenStreetMap Integration

- Each tile overlays corresponding geographical area from OpenStreetMap
- Tile borders align with H3 grid boundaries
- Map features visible through semi-transparent tile backgrounds

### 5.4 Vue.js Implementation

- **Component Structure**:
  - `App.vue`: Main application container
  - `TileMap.vue`: Manages the map and tile rendering using Leaflet
  - `Tile.vue`: Individual tile component with content display
  - `TileNavigation.vue`: Controls for navigating between tiles and resolution levels

- **State Management**:
  - Vuex store for managing tile data and application state
  - Reactive properties for handling tile selection and transitions

- **H3 Integration**:
  - h3-js library used for frontend hexagonal grid calculations
  - Coordinate conversion between H3 indices and Leaflet map coordinates
  - Polygon generation for rendering hexagonal and pentagonal tiles

- **Styling**:
  - CSS Grid or Flexbox for layout
  - SVG for tile borders and custom styling
  - Vue transitions for smooth tile navigation effects

## 6. Implementation Plan

### 6.1 Phase 1: Core Backend
- Set up FastAPI project structure
- Implement H3 integration
- Develop Tile, HexagonTile, and PentagonTile classes
- Implement file-based storage system

### 6.2 Phase 2: API Development
- Implement RESTful endpoints
- Add validation and error handling
- Create API documentation

### 6.3 Phase 3: Frontend Development
- Design and implement UI components
- Integrate with OpenStreetMap
- Implement tile navigation and transitions

### 6.4 Phase 4: Testing and Refinement
- Unit and integration testing
- Performance optimization
- Documentation

## 7. Technology Stack

- **Backend**: Python 3.12, FastAPI, H3 Python bindings
- **Frontend**: HTML5, CSS3, Vue.js, Leaflet.js, h3-js
- **Map Integration**: OpenStreetMap, Leaflet.js
- **Data Storage**: File-based JSON
- **Development Tools**: Git, Poetry (dependency management)

## 8. Extension Points

The framework is designed to be extended in the following ways:

- **Custom Tile Types**: Developers can create new tile types by extending the base Tile class
- **Content Processors**: Add specialized handlers for different types of content
- **Game Mechanics**: Implement game-specific rules and mechanics
- **Alternative Storage**: Replace file-based storage with database solutions
- **Enhanced Visualization**: Add custom rendering for specific tile types

## 9. Limitations and Considerations

- File-based storage may have performance limitations with large numbers of tiles
- Initial version focuses on basic functionality; advanced features will be added in future iterations
- Mobile responsiveness will require additional design considerations
