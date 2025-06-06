# HexGlobe

A web application that implements a hexagonal grid mapping system using HTML5 Canvas for visualization.

## Overview

HexGlobe provides a framework for visualizing and interacting with a hexagonal grid. It creates a grid of hexagonal tiles that can be used for various applications including games, data visualization, and geographic analysis.

## Features

- Hexagonal tile visualization using HTML5 Canvas
- Dynamic grid sizing that fills the available space
- Interactive tile navigation with click support
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

## Technology Stack

### Backend
- Python 3.12
- FastAPI
- H3 Python bindings
- JSON-based file storage

### Frontend
- Vanilla JavaScript
- HTML5 Canvas for rendering
- h3-js for hexagonal grid calculations
- HTML5/CSS3
- Fetch API for backend communication

### Data Storage
- File-based JSON storage

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
│   └── tiles/              # JSON storage for tile data
├── frontend/
│   ├── css/
│   │   └── styles.css      # Main stylesheet
│   ├── js/
│   │   ├── app.js          # Main application logic
│   │   ├── hexTile.js      # Canvas-based hexagon rendering module
│   │   └── navigation.js   # Tile navigation and API communication
│   └── index.html          # Main HTML entry point
└── README.md               # This file
```

## Core Components

### HexTile.js
Handles the rendering of individual hexagonal tiles using HTML5 Canvas. Each tile includes:
- Border and fill styling
- Grid pattern to simulate map data
- Tile information display
- Point containment detection for interaction

### app.js
Main application logic that:
- Sets up the canvas and event listeners
- Calculates grid dimensions to fill available space
- Manages the active tile state
- Handles rendering and updates
- Controls zoom level and H3 resolution
- Converts between different H3 resolutions
- Integrates with the navigation system for API calls

### navigation.js
Manages tile navigation and backend communication:
- Loads tile data from the backend API
- Manages neighbor relationships
- Handles navigation between tiles
- Provides fallback functionality when API is unavailable
- Dispatches events when tile data changes

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
- `PUT /api/tiles/{tile_id}`: Update tile information
- `GET /api/tiles/{tile_id}/neighbors`: Get neighboring tiles
- `GET /api/tiles/{tile_id}/parent`: Get parent tile
- `GET /api/tiles/{tile_id}/children`: Get child tiles
- `GET /api/tiles/{tile_id}/resolutions`: Get resolution IDs for the tile
- `POST /api/tiles/{tile_id}/move-content/{target_id}`: Move content to target tile
- `PUT /api/tiles/{tile_id}/visual`: Update visual properties
- `GET /api/tiles/{tile_id}/grid`: Get a 2D grid of H3 indexes centered around the specified tile

## Tile Data Structure

Each tile is stored as a JSON file with the following structure:

```json
{
  "id": "8928308280fffff",
  "content": "Sample content",
  "visual_properties": {
    "border_color": "#FF0000",
    "border_thickness": 2,
    "border_style": "solid",
    "fill_color": "#FFFFFF",
    "fill_opacity": 0.5
  },
  "parent_id": "8828308280fffff",
  "children_ids": ["...array of child IDs..."],
  "neighbors": {
    "bottom_middle": "...neighbor ID...",
    "bottom_left": "...neighbor ID...",
    "bottom_right": "...neighbor ID...",
    "top_left": "...neighbor ID...",
    "top_middle": "...neighbor ID...",
    "top_right": "...neighbor ID..."
  },
  "resolution_ids": {
    "0": "8000000000000",
    "1": "8100000000000",
    "...": "...",
    "15": "8f00000000000"
  }
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Uber H3](https://github.com/uber/h3) - Hexagonal hierarchical geospatial indexing system
- [HTML5 Canvas](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API) - For rendering the hexagonal grid
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for building APIs with Python
