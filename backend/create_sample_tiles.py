#!/usr/bin/env python
"""
Script to create sample tile data for HexGlobe.
This will generate a set of tiles at a specific resolution around a center point.
"""

import os
import json
import h3
from hexglobe.models.tile import DATA_DIR, TileData, VisualProperties

def create_sample_tiles():
    """Create sample tile data for testing."""
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Define center point (San Francisco)
    lat, lng = 37.7749, -122.4194
    
    # Generate tiles at resolution 2 (large hexagons)
    center_index = h3.geo_to_h3(lat, lng, 2)
    
    # Get a ring of tiles around the center
    tile_indices = h3.k_ring(center_index, 2)
    
    # Create sample data for each tile
    for i, index in enumerate(tile_indices):
        # Check if it's a pentagon
        is_pentagon = h3.h3_is_pentagon(index)
        
        # Create visual properties with different colors
        visual_props = VisualProperties(
            border_color="#000000",
            border_thickness=2,
            border_style="solid",
            fill_color=f"#{(i * 20) % 256:02x}{(i * 40) % 256:02x}{(i * 60) % 256:02x}",
            fill_opacity=0.7
        )
        
        # Create tile data
        tile_data = TileData(
            id=index,
            content=f"Sample content for {'pentagon' if is_pentagon else 'hexagon'} {index}",
            visual_properties=visual_props,
            parent_id=h3.h3_to_parent(index, h3.h3_get_resolution(index) - 1) if h3.h3_get_resolution(index) > 0 else None,
            children_ids=h3.h3_to_children(index, h3.h3_get_resolution(index) + 1)
        )
        
        # Save to file
        file_path = os.path.join(DATA_DIR, f"{index}.json")
        with open(file_path, 'w') as f:
            f.write(tile_data.model_dump_json(indent=2))
        
        print(f"Created tile: {index} ({'pentagon' if is_pentagon else 'hexagon'})")
    
    print(f"Created {len(tile_indices)} sample tiles in {DATA_DIR}")
    print(f"Center tile ID: {center_index}")

if __name__ == "__main__":
    create_sample_tiles()
