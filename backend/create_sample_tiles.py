#!/usr/bin/env python
"""
Script to create sample tile data for HexGlobe.
This will generate a set of tiles at a specific resolution around a center point.
"""

import os
import json
import h3
from hexglobe.models.tile import TileData, VisualProperties
from hexglobe.models.tile import HexagonTile, PentagonTile

def create_sample_tiles():
    """Create sample tile data for testing."""
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
        
        # Create the appropriate tile type
        if is_pentagon:
            tile = PentagonTile(index, f"Sample content for pentagon {index}")
        else:
            tile = HexagonTile(index, f"Sample content for hexagon {index}")
            
        # Set visual properties
        for prop_name, prop_value in visual_props.dict().items():
            tile.set_visual_property(prop_name, prop_value)
            
        # Save using the new split format methods
        tile.save_static()
        
        # For demonstration, only add content to even-indexed tiles
        if i % 2 == 0:
            tile.save_dynamic()
        else:
            # For odd-indexed tiles, set empty content to demonstrate dynamic file not being created
            tile.content = ""
            # Reset visual properties to defaults
            tile.visual_properties = VisualProperties()
            tile.save_dynamic()
        
        print(f"Created tile: {index} ({'pentagon' if is_pentagon else 'hexagon'})")
    
    print(f"Created {len(tile_indices)} sample tiles")
    print(f"Center tile ID: {center_index}")

if __name__ == "__main__":
    create_sample_tiles()
