# HexGlobe Design Document

## 1. Project Overview

HexGlobe is a web application framework that implements a global hexagonal grid system using Uber's H3 library. It provides a platform for developers to build applications on top of a hexagonal/pentagonal tile-based world map. The framework offers a 2D representation of the world with interactive tiles that can store content and be navigated by users.

## 2. System Architecture

### 2.1 High-Level Architecture

```
+-------------------+      +-------------------+      +-------------------+
|                   |      |                   |      |                   |
|  Frontend         |      |  Backend API      |      |  Tile Storage     |
|  (Vue.js)         +----->+  (Python/FastAPI) +----->+  (JSON Files)     |
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
- **HexTile Component**: Canvas-based hexagon rendering with grid pattern and debug info
- **Navigation Controls**: Allows users to navigate between tiles and change resolution levels

### 5.2 Interaction Flow

1. User loads the application, which displays the default active tile
2. Neighboring tiles are visible around the active tile
3. User clicks on a neighboring tile
4. The clicked tile becomes the active tile with a smooth transition
5. The view updates to show the new active tile and its neighbors

### 5.3 Visualization Approach

#### Current Implementation
- Pure Canvas-based hexagon rendering
- Grid pattern inside hexagons to simulate map data
- Debug information panel showing tile details
- Neighbor visualization with toggle functionality

#### Future Map Integration
- Each hexagon will be filled with corresponding map data
- Custom rendering of map features within hexagon boundaries
- Potential for different map styles or data sources per hexagon

### 5.4 Vue.js Implementation

- **Component Structure**:
  - `App.vue`: Main application container
  - `HomeView.vue`: Main view component
  - `HexTile.vue`: Canvas-based hexagon rendering component
  - `TileNavigation.vue`: Controls for navigating between tiles

- **State Management**:
  - Pinia store for managing tile data and application state
  - Reactive properties for handling tile selection and transitions

- **H3 Integration**:
  - h3-js library used for frontend hexagonal grid calculations
  - Neighbor calculation and resolution management
  - Coordinate conversion for proper hexagon rendering

## 6. Implementation Progress

### 6.1 Completed
- Set up FastAPI backend with CORS configuration
- Implemented Tile model with H3 integration
- Created basic API endpoints for tile operations
- Developed Canvas-based hexagon visualization
- Implemented neighbor visualization
- Set up GitHub repository and version control

### 6.2 In Progress
- Enhancing hexagon interaction capabilities
- Implementing tile navigation system
- Improving debug information display

### 6.3 Next Steps
- Implement click navigation between hexagons
- Add smooth transitions between tiles
- Prepare for map data integration
- Enhance the backend API for more complex tile operations

### 6.4 Future Enhancements
- Add zooming to show different H3 resolution levels
- Implement map data rendering within hexagons
- Add content editing and management features
- Develop game mechanics or application-specific features

## 7. Technology Stack

- **Backend**: Python 3.12, FastAPI, H3 Python bindings
- **Frontend**: Vue.js, HTML5 Canvas, h3-js
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
