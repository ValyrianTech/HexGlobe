# HexGlobe

A web application that implements a generic game board framework using hexagonal grid mapping based on Uber's H3 library.

## Overview

HexGlobe provides a framework for visualizing and interacting with a global hexagonal grid. It uses H3, a hierarchical geospatial indexing system, to create a grid of hexagonal tiles that can be used for various applications including games, data visualization, and geographic analysis.

## Features

- Hexagonal tile visualization using HTML5 Canvas
- Integration with Uber's H3 library for hexagonal grid calculations
- Hierarchical resolution system for parent-child relationships between tiles
- Neighbor visualization and navigation
- Customizable visual properties (border color, thickness, style)
- Debug information display

## Technology Stack

### Backend
- Python 3.12
- FastAPI
- H3 Python bindings

### Frontend
- Vue.js
- h3-js for hexagonal grid calculations
- HTML5 Canvas for rendering
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
cd backend
poetry install
```

#### Frontend

```bash
cd frontend
npm install
```

### Running the Application

#### Backend

```bash
cd backend
poetry run python run.py
```

#### Frontend

```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:3001` by default.

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
│   ├── public/            # Static files
│   ├── src/
│   │   ├── components/    # Vue components
│   │   ├── views/         # Vue views
│   │   ├── store/         # Pinia stores
│   │   ├── App.vue        # Root component
│   │   └── main.js        # Entry point
│   ├── package.json       # JavaScript dependencies
│   └── vite.config.js     # Vite configuration
└── README.md              # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Uber H3](https://github.com/uber/h3) - Hexagonal hierarchical geospatial indexing system
- [Vue.js](https://vuejs.org/) - The Progressive JavaScript Framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for building APIs with Python
