# HexGlobe

A web application that implements a hexagonal grid mapping system using HTML5 Canvas for visualization.

## Overview

HexGlobe provides a framework for visualizing and interacting with a hexagonal grid. It creates a grid of hexagonal tiles that can be used for various applications including games, data visualization, and geographic analysis.

## Features

- Hexagonal tile visualization using HTML5 Canvas
- Dynamic grid sizing that fills the available space
- Interactive tile navigation with click support
- Multi-selection of tiles with toggle behavior
- Focus tile tracking (last selected tile) with distinct visual styling
- Selected tiles tracking and visual highlighting
- Conditional navigation button for selected tiles
- Neighbor visualization and highlighting
- Customizable visual properties (border color, thickness, style)
- Zoom control slider (1-10) to adjust visible hex tiles
- H3 resolution slider (0-15) to adjust hexagon size on Earth's surface
- Tile information display
- Backend API integration for tile data persistence
- Comprehensive logging for debugging
- Automatic tile creation and storage
- Position-based neighbor references with descriptive keys (top_left, top_middle, etc.)
- Consistent clockwise ordering of neighbor tiles
- Multi-resolution tile mapping (same location at different H3 resolutions)
- Flat-bottom hexagon orientation with proper grid alignment
- Consistent coordinate system using (row, col) format
- Calibrated hexagon map images with precise alignment
- Transformation pipeline for correcting map projection distortion
- Visual calibration aids for verification and debugging
- "Go To" navigation for direct access to locations by H3 index or address
- Mod system for creating custom applications on the same grid infrastructure
- Timestamp-based versioning system for hex map images
- Automatic retrieval and display of the latest map version for each tile

## Technology Stack

### Backend
- Python 3.12
- FastAPI
- H3 Python bindings
- JSON-based file storage

### Frontend
- Vanilla JavaScript
- HTML5 Canvas for rendering
- HTML5/CSS3
- Fetch API for backend communication

### Data Storage
- File-based JSON storage
- Split storage architecture:
  - Static data: Grid structure and relationships
  - Dynamic data: Content and visual properties
  - Map images: Timestamped versions for historical tracking

## Getting Started

### Prerequisites

- Node.js (v16+)
- Python 3.12
- Poetry (for Python dependency management)

### Installation

#### Backend

```bash
# Create and activate virtual environment (from project root)
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
cd backend
poetry install
cd ..
```

#### Frontend

```bash
# With virtual environment activated
cd frontend
# No build step needed - pure HTML/CSS/JS implementation
```

### Running the Application

#### Backend

```bash
# With virtual environment activated
cd backend
python run.py
```

The backend API will be available at `http://localhost:8000` by default.

#### Frontend

Simply open the `frontend/index.html` file in your browser, or serve it using a simple HTTP server:

```bash
# With virtual environment activated
cd frontend
python -m http.server 8080
```

The application will be available at `http://localhost:8080` by default.

## Project Structure

```
HexGlobe/
├── backend/
│   ├── hexglobe/
│   │   ├── api/
│   │   │   └── tiles.py    # API endpoints for tile operations
│   │   ├── models/
│   │   │   └── tile.py     # Tile data models and storage
│   │   └── main.py         # FastAPI application setup
│   ├── pyproject.toml      # Python dependencies
│   └── run.py              # Entry point
├── data/
│   ├── static/             # Static tile data (H3 grid information)
│   │   └── res_X/          # Organized by resolution level
│   │       └── ...         # Nested directories by H3 index segments
│   ├── dynamic/            # Dynamic tile data (content and visual properties)
│   │   └── default/        # Default mod/application
│   │       └── res_X/      # Organized by resolution level
│   │           └── ...     # Nested directories by H3 index segments
│   └── hex_maps/           # Generated hexagon map images
│       └── res_X/          # Organized by resolution level
│           └── ...         # Nested directories by H3 index segments
├── frontend/
│   ├── assets/
│   │   └── generate_hex_map.py  # Map image generation script
│   ├── css/
│   │   └── styles.css      # Main stylesheet
│   ├── js/
│   │   ├── app.js          # Main application logic
│   │   ├── hexTile.js      # Canvas-based hexagon rendering module
│   │   ├── navigation.js   # Tile navigation and API communication
│   │   └── modLoader.js    # Mod loading and management
│   ├── index.html          # Main HTML entry point
│   └── mods/               # Symbolic link to root mods directory
├── mods/                   # Mod directory containing all available mods
│   ├── default/            # Default mod (fallback)
│   │   ├── manifest.json   # Mod metadata
│   │   ├── css/            # Mod-specific CSS
│   │   ├── js/             # Mod-specific JavaScript
│   │   └── README.md       # Mod documentation
│   └── test/               # Test mod for verification
│       ├── manifest.json   # Mod metadata
│       ├── css/            # Mod-specific CSS
│       ├── js/             # Mod-specific JavaScript
│       └── README.md       # Mod documentation
└── README.md               # This file
```

## Core Components

### HexTile.js
Handles the rendering of individual hexagonal tiles using HTML5 Canvas. Each tile includes:
- Border and fill styling
- Grid pattern to simulate map data
- Tile information display
- Point containment detection for interaction
- Flat-bottom hexagon orientation (starting angle of 0 radians)
- Proper vertex calculation for consistent hexagon shape

### app.js
Main application logic that:
- Sets up the canvas and event listeners
- Calculates grid dimensions to fill available space
- Manages the active tile state
- Tracks selected tiles and provides visual feedback
- Maintains a focus tile (last selected tile) with distinct visual styling
- Implements tile selection toggle behavior
- Shows a navigation button when exactly one tile is selected
- Handles rendering and updates
- Controls zoom level and H3 resolution
- Converts between different H3 resolutions
- Integrates with the navigation system for API calls
- Implements proper coordinate system using (row, col) format
- Applies correct vertical offset for odd columns to maintain hexagonal grid alignment
- Provides "Go To" functionality for navigating to locations by H3 index or address

### navigation.js
Manages tile navigation and backend communication:
- Loads tile data from the backend API
- Manages neighbor relationships
- Handles navigation between tiles
- Provides fallback functionality when API is unavailable
- Dispatches events when tile data changes
- Includes mod_name parameter in all API calls

### modLoader.js
Handles the loading and management of mods:
- Parses URL parameters to determine which mod to load
- Dynamically loads mod assets (CSS and JavaScript)
- Provides a global interface for accessing the current mod name
- Falls back to the default mod if loading fails
- Dispatches events when a mod is loaded
- Provides utility methods for API URL construction

### generate_hex_map.py
Generates precisely calibrated hexagonal map images for H3 tiles:
- Renders OpenStreetMap data for the geographic area of each H3 hexagon
- Rotates and aligns maps to match flat-bottom hexagon orientation
- Applies vertical scaling to correct for projection distortion
- Applies horizontal skew to further improve vertex alignment
- Draws calibration aids (concentric hexagons and reference dots)
- Supports debug mode for displaying intermediate images and vertex coordinates
- Ensures seamless boundaries between adjacent hexagon tiles

## H3 Integration

HexGlobe uses Uber's H3 library for hexagonal grid operations:

- **H3 Indexes**: Each tile is identified by an H3 index (e.g., `87000000fffffff`)
- **Resolution Levels**: H3 supports resolutions 0-15, where:
  - Lower resolutions (0-2): Very large hexagons covering large areas
  - Medium resolutions (3-9): Moderate-sized hexagons for regional analysis
  - Higher resolutions (10-15): Small hexagons for detailed local analysis
- **Zoom vs. Resolution**:
  - Zoom level (1-10): Controls how many hexagons are visible on screen
  - H3 Resolution (0-15): Controls the actual size of each hexagon on Earth's surface
- **Neighbor Ordering**:
  - Neighbors are stored in a dictionary with descriptive position keys
  - Position keys follow a flat-bottom hexagon orientation (bottom_middle, bottom_left, top_left, etc.)
  - Positions are determined based on geographic orientation relative to the equator
  - For pentagons, the missing position is marked with "pentagon"
  - This provides a consistent and intuitive way to access specific neighbors by their relative position
- **Resolution Mapping**:
  - Each tile stores IDs for the same geographic location at all H3 resolutions (0-15)
  - Lower resolutions are computed by walking up the parent hierarchy
  - Higher resolutions are computed by converting geographic coordinates to H3 indexes

## API Endpoints

The backend provides the following RESTful API endpoints:

- `GET /api/tiles/{tile_id}`: Get tile information
  - Query parameter: `mod_name` (optional, default: "default")
- `PUT /api/tiles/{tile_id}`: Update tile information
  - Query parameter: `mod_name` (optional, default: "default")
- `GET /api/tiles/{tile_id}/neighbors`: Get neighboring tiles
  - Query parameter: `mod_name` (optional, default: "default")
- `GET /api/tiles/{tile_id}/parent`: Get parent tile
  - Query parameter: `mod_name` (optional, default: "default")
- `GET /api/tiles/{tile_id}/children`: Get child tiles
  - Query parameter: `mod_name` (optional, default: "default")
- `GET /api/tiles/{tile_id}/resolutions`: Get resolution IDs for the tile
  - Query parameter: `mod_name` (optional, default: "default")
- `POST /api/tiles/{tile_id}/move-content/{target_id}`: Move content to target tile
  - Query parameter: `mod_name` (optional, default: "default")
- `PUT /api/tiles/{tile_id}/visual`: Update visual properties
  - Query parameter: `mod_name` (optional, default: "default")
- `GET /api/tiles/{tile_id}/grid`: Get a 2D grid of H3 indexes centered around the specified tile
  - Query parameter: `mod_name` (optional, default: "default")
- `POST /api/tiles/{tile_id}/generate-map`: Generate a map image for a specific tile (with timestamp)

## Using the Mod System

HexGlobe includes a mod system that allows you to create custom applications on top of the same hexagonal grid infrastructure. Each mod can have its own visual styling, behavior, and data storage.

### Loading a Mod

To load a specific mod, add the `mod_name` parameter to the URL:

```
http://localhost:8080/?mod_name=test
```

If no mod_name parameter is provided, the default mod will be loaded.

### Available Mods

- **default**: The standard HexGlobe experience with black borders and white backgrounds
- **test**: A test mod with purple borders and light blue backgrounds

### Creating a New Mod

To create a new mod:

1. Copy the default mod directory:
   ```bash
   cp -r mods/default mods/your_mod_name
   ```

2. Edit the manifest.json file:
   ```json
   {
     "name": "Your Mod Name",
     "version": "1.0.0",
     "description": "Description of your mod",
     "author": "Your Name",
     "theme": "css/theme.css",
     "script": "js/mod.js"
   }
   ```

3. Customize the CSS in `css/theme.css` to change the visual appearance
4. Modify the JavaScript in `js/mod.js` to implement custom behavior
5. Update the README.md to document your mod

### Mod Structure

Each mod follows a standard directory structure:

```
your_mod_name/
├── manifest.json    # Mod metadata and configuration
├── css/
│   └── theme.css    # Theme CSS that can be customized
├── js/
│   └── mod.js       # Mod logic and event handlers
└── README.md        # Documentation
```

### Event Handling

Your mod's JavaScript can listen for the following events:

```javascript
// Initialize when the mod is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Your initialization code here
});

// Listen for tile selection events
document.addEventListener('tileSelected', (event) => {
  const tileId = event.detail.tileId;
  // Your tile selection handling code here
});

// Listen for active tile changes
document.addEventListener('activeTileChanged', (event) => {
  const tileId = event.detail.tileId;
  // Your active tile change handling code here
});

// Listen for tile content updates
document.addEventListener('tileContentUpdated', (event) => {
  const tileId = event.detail.tileId;
  const content = event.detail.content;
  // Your content update handling code here
});
```

## Usage

### Basic Navigation

1. When the application loads, you'll see a grid of hexagonal tiles with the active tile highlighted in the center.
2. Click on any tile to select it. Selected tiles will be highlighted with an orange border and yellow fill.
3. Click on a selected tile to unselect it.
4. You can select multiple tiles to compare them.
5. When exactly one tile is selected, a "Navigate to Selected Tile" button will appear in the debug panel.
6. Click this button to make the selected tile the new active tile, which will center the grid on that tile.
7. Use the zoom slider to adjust how many tiles are visible on screen.
8. Use the resolution slider to change the size of the hexagons on Earth's surface.

### Debug Panel

The debug panel on the right side of the screen provides information about:
- The active tile's H3 index
- Resolution information (backend and frontend)
- Current zoom level
- Grid position of the active tile
- Tile content (if available)
- List of currently selected tiles
- Navigation button (when exactly one tile is selected)

## Tile Data Structure

Each tile's data is split into static and dynamic components:

### Static Data (H3 grid information)
```json
{
  "id": "8928308280fffff",
  "parent_id": "8828308280fffff",
  "children_ids": [...],
  "neighbor_ids": {...},
  "resolution_ids": {...},
  "resolution": 9
}
```

### Dynamic Data (Content and visual properties)
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

Dynamic data files are only created when there's actual content or non-default visual properties.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Uber H3](https://github.com/uber/h3) - Hexagonal hierarchical geospatial indexing system
- [HTML5 Canvas](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API) - For rendering the hexagonal grid
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for building APIs with Python
