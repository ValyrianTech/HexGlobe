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
- Tile information display

## Technology Stack

### Backend
- Python 3.12
- FastAPI
- H3 Python bindings

### Frontend
- Vanilla JavaScript
- HTML5 Canvas for rendering
- h3-js for hexagonal grid calculations
- HTML5/CSS3

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
│   │   ├── main.py        # FastAPI application
│   │   ├── models/        # Data models
│   │   └── services/      # Business logic
│   ├── pyproject.toml     # Python dependencies
│   └── run.py             # Entry point
├── frontend/
│   ├── css/
│   │   └── styles.css     # Main stylesheet
│   ├── js/
│   │   ├── app.js         # Main application logic
│   │   ├── hexTile.js     # Canvas-based hexagon rendering module
│   │   └── navigation.js  # Tile navigation and neighbor management
│   └── index.html         # Main HTML entry point
└── README.md              # This file
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

### navigation.js
Manages tile navigation including:
- Loading tile data from the API
- Managing neighbor relationships
- Handling navigation between tiles
- Providing fallback functionality for development

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Uber H3](https://github.com/uber/h3) - Hexagonal hierarchical geospatial indexing system
- [HTML5 Canvas](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API) - For rendering the hexagonal grid
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for building APIs with Python
