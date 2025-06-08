#!/usr/bin/env python3
"""
HexGlobe Map Generator

This script generates map images for HexGlobe hexagons using OpenStreetMap data.
It takes an H3 index, fetches the corresponding map data, and creates an image
with the hexagon boundary drawn at the exact geographic coordinates.

Usage:
    python generate_hex_map.py --h3_index 8928308280fffff
"""

import argparse
import h3
import os
import math
from PIL import Image
from staticmap import StaticMap, Line
import numpy as np
import json

# Constants for the image rendering
CANVAS_SIZE = 1024
HEXAGON_BORDER_WIDTH = 5
HEXAGON_BORDER_COLOR = "#00FF00"  # Green border for visibility


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate map images for HexGlobe hexagons.')
    parser.add_argument('--h3_index', required=True, help='H3 index of the tile')
    parser.add_argument('--output', default=None, help='Output file path (default: h3_index.png)')
    parser.add_argument('--zoom', type=int, default=None, 
                        help='OpenStreetMap zoom level (1-19, default: auto-calculated)')
    parser.add_argument('--vertices', action='store_true',
                        help='Output the pixel coordinates of the hexagon vertices')
    return parser.parse_args()


def calculate_zoom_level(boundary):
    """
    Calculate an appropriate zoom level based on the hexagon size.
    
    Args:
        boundary: List of [lat, lng] boundary points
        
    Returns:
        Zoom level (1-19)
    """
    # Calculate the maximum distance between any two points
    max_distance = 0
    for i in range(len(boundary)):
        for j in range(i+1, len(boundary)):
            lat1, lng1 = boundary[i]
            lat2, lng2 = boundary[j]
            
            # Haversine formula for distance
            R = 6371  # Earth radius in km
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            
            max_distance = max(max_distance, distance)
    
    # Estimate zoom level based on distance - increased zoom levels for better detail
    if max_distance > 1000:  # > 1000 km
        return 5  # Was 3
    elif max_distance > 500:
        return 7  # Was 5
    elif max_distance > 100:
        return 9  # Was 7
    elif max_distance > 50:
        return 11  # Was 9
    elif max_distance > 10:
        return 13  # Was 11
    elif max_distance > 5:
        return 15  # Was 13
    elif max_distance > 1:
        return 17  # Was 15
    else:
        return 19  # Was 17


def geo_to_pixel(lat, lng, center_lat, center_lng, zoom):
    """
    Convert geographic coordinates to pixel coordinates in the image.
    
    Args:
        lat: Latitude
        lng: Longitude
        center_lat: Center latitude of the map
        center_lng: Center longitude of the map
        zoom: Zoom level
        
    Returns:
        (x, y) pixel coordinates
    """
    # Web Mercator projection formulas
    def lat_to_y(lat):
        return 128 / math.pi * 2**zoom * (math.pi - math.log(math.tan(math.pi / 4 + lat * math.pi / 360)))
    
    def lng_to_x(lng):
        return 128 / math.pi * 2**zoom * (lng + 180) / 360
    
    # Calculate center pixel
    center_x = lng_to_x(center_lng)
    center_y = lat_to_y(center_lat)
    
    # Calculate target pixel
    x = lng_to_x(lng)
    y = lat_to_y(lat)
    
    # Calculate relative position from center
    rel_x = x - center_x + CANVAS_SIZE / 2
    rel_y = y - center_y + CANVAS_SIZE / 2
    
    return (int(rel_x), int(rel_y))


def create_hexagon_map(h3_index, zoom=None):
    """
    Create a map image with a hexagon boundary for the given H3 index.
    
    Args:
        h3_index: H3 index of the tile
        zoom: OpenStreetMap zoom level (optional)
        
    Returns:
        Tuple of (PIL Image object, list of vertex pixel coordinates)
    """
    # Validate the H3 index
    if not h3.h3_is_valid(h3_index):
        raise ValueError(f"Invalid H3 index: {h3_index}")
    
    # Check if it's a hexagon (not a pentagon)
    if h3.h3_is_pentagon(h3_index):
        raise ValueError(f"Pentagon tiles are not supported: {h3_index}")
    
    # Get center coordinates and boundary of the hexagon
    center_lat, center_lng = h3.h3_to_geo(h3_index)
    boundary = h3.h3_to_geo_boundary(h3_index)
    
    # Calculate zoom level if not provided
    if zoom is None:
        zoom = calculate_zoom_level(boundary)
        # Increase zoom by 1 to make hexagon larger in the frame
        zoom = min(max(zoom + 1, 1), 19)  # Ensure zoom is between 1 and 19
    
    # Create a static map centered on the hexagon
    m = StaticMap(CANVAS_SIZE, CANVAS_SIZE)
    
    # Convert the boundary to a list of (lng, lat) tuples for the Line
    line_points = [(lng, lat) for lat, lng in boundary]
    
    # Create a closed polygon by adding the first point at the end
    line_points.append(line_points[0])
    
    # Add the hexagon boundary to the map
    line = Line(line_points, HEXAGON_BORDER_COLOR, HEXAGON_BORDER_WIDTH)
    m.add_line(line)
    
    # Render the map with the hexagon boundary
    image = m.render(zoom=zoom, center=[center_lng, center_lat])
    
    # Calculate pixel coordinates of vertices
    pixel_vertices = []
    for lat, lng in boundary:
        pixel_x, pixel_y = geo_to_pixel(lat, lng, center_lat, center_lng, zoom)
        pixel_vertices.append((pixel_x, pixel_y))
    
    return image, pixel_vertices


def main():
    """Main function."""
    args = parse_arguments()
    
    try:
        # Create the map image
        img, vertices = create_hexagon_map(args.h3_index, args.zoom)
        
        # Determine output path
        output_path = args.output if args.output else f"{args.h3_index}.png"
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Save the image
        img.save(output_path, format='PNG')
        print(f"Map image saved to {output_path}")
        
        # Output vertex coordinates if requested
        if args.vertices:
            vertices_file = f"{os.path.splitext(output_path)[0]}_vertices.json"
            with open(vertices_file, 'w') as f:
                json.dump({
                    'h3_index': args.h3_index,
                    'image_size': CANVAS_SIZE,
                    'vertices': vertices
                }, f, indent=2)
            print(f"Vertex coordinates saved to {vertices_file}")
            
            # Also print to console for convenience
            print("\nHexagon Vertices (x, y):")
            for i, (x, y) in enumerate(vertices):
                print(f"Vertex {i}: ({x}, {y})")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
