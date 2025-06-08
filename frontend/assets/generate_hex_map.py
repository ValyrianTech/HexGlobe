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
    parser.add_argument('--no-rotate', action='store_true',
                        help='Skip rotation to flat-bottom orientation')
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
    def lat_to_y(lat_deg):
        lat_rad = math.radians(lat_deg)
        y = 128 / math.pi * 2**zoom * (math.pi - math.log(math.tan(math.pi / 4 + lat_rad / 2)))
        return y
    
    def lng_to_x(lng_deg):
        x = 128 / math.pi * 2**zoom * math.radians(lng_deg + 180)
        return x
    
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


def calculate_bearing(lat1, lng1, lat2, lng2):
    """
    Calculate the bearing from point 1 to point 2.
    All angles in degrees.
    """
    # Convert to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Calculate bearing
    y = math.sin(lng2 - lng1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lng2 - lng1)
    bearing = math.atan2(y, x)
    
    # Convert to degrees
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing


def calculate_flat_bottom_rotation(vertices):
    """
    Calculate the rotation angle needed to make the hexagon flat-bottomed
    based on the pixel coordinates of the vertices.
    
    Args:
        vertices: List of (x, y) vertex coordinates
        
    Returns:
        Rotation angle in degrees
    """
    # A hexagon has 6 vertices and 6 edges
    # We need to find which edge should be the bottom edge
    
    # For each pair of adjacent vertices, calculate the midpoint's y-coordinate
    edge_midpoints = []
    for i in range(len(vertices)):
        next_i = (i + 1) % len(vertices)
        v1 = vertices[i]
        v2 = vertices[next_i]
        midpoint = ((v1[0] + v2[0]) / 2, (v1[1] + v2[1]) / 2)
        edge_midpoints.append((i, midpoint))
    
    # Find the edge with the largest y-coordinate (lowest on screen)
    bottom_edge_idx, bottom_midpoint = max(edge_midpoints, key=lambda x: x[1][1])
    
    # Get the two vertices of this edge
    v1_idx = bottom_edge_idx
    v2_idx = (bottom_edge_idx + 1) % len(vertices)
    
    v1 = vertices[v1_idx]
    v2 = vertices[v2_idx]
    
    # Ensure v1 is to the left of v2
    if v1[0] > v2[0]:
        v1, v2 = v2, v1
    
    # Calculate the angle of this edge with the horizontal
    dx = v2[0] - v1[0]
    dy = v2[1] - v1[1]
    
    # Calculate the angle in radians and convert to degrees
    angle = math.degrees(math.atan2(dy, dx))
    
    # We want this angle to be 0 (horizontal), so rotate by -angle
    return -angle


def rotate_image_and_vertices(image, vertices, angle, center=None):
    """
    Rotate the image and vertex coordinates.
    
    Args:
        image: PIL Image object
        vertices: List of (x, y) vertex coordinates
        angle: Rotation angle in degrees (clockwise)
        center: Center of rotation (x, y), defaults to image center
        
    Returns:
        Tuple of (rotated image, rotated vertices)
    """
    if center is None:
        center = (image.width // 2, image.height // 2)
    
    # Convert angle to radians (PIL uses counter-clockwise rotation)
    angle_rad = -math.radians(angle)
    
    # Rotate the image
    rotated_image = image.rotate(angle, resample=Image.BICUBIC, expand=False)
    
    # Rotate the vertices
    rotated_vertices = []
    for x, y in vertices:
        # Translate to origin
        x_shifted = x - center[0]
        y_shifted = y - center[1]
        
        # Rotate
        x_rotated = x_shifted * math.cos(angle_rad) - y_shifted * math.sin(angle_rad)
        y_rotated = x_shifted * math.sin(angle_rad) + y_shifted * math.cos(angle_rad)
        
        # Translate back
        x_final = round(x_rotated + center[0])
        y_final = round(y_rotated + center[1])
        
        rotated_vertices.append((x_final, y_final))
    
    return rotated_image, rotated_vertices


def create_hexagon_map(h3_index, zoom=None, rotate=True):
    """
    Create a map image with a hexagon boundary for the given H3 index.
    
    Args:
        h3_index: H3 index of the tile
        zoom: OpenStreetMap zoom level (optional)
        rotate: Whether to rotate the image to flat-bottom orientation
        
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
    
    # Draw all vertices on the image with labels
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(image)
    
    # Draw circles at all vertices
    colors = ["red", "orange", "yellow", "green", "blue", "purple"]
    radius = 10
    
    for i, vertex in enumerate(pixel_vertices):
        draw.ellipse((vertex[0]-radius, vertex[1]-radius, vertex[0]+radius, vertex[1]+radius), fill=colors[i % len(colors)])
    
    # Draw text labels with coordinates
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font = ImageFont.load_default()
    
    for i, vertex in enumerate(pixel_vertices):
        draw.text((vertex[0]+radius, vertex[1]-radius), f"{i}: ({vertex[0]}, {vertex[1]})", fill=colors[i % len(colors)], font=font)
    
    # Draw lines connecting the vertices in order
    for i in range(len(pixel_vertices)):
        next_i = (i + 1) % len(pixel_vertices)
        draw.line([pixel_vertices[i], pixel_vertices[next_i]], fill="white", width=2)
    
    # Save the unrotated image for reference
    unrotated_image = image.copy()
    unrotated_image.save(f"{h3_index}_vertices.png")
    print(f"Image with labeled vertices saved to {h3_index}_vertices.png")
    
    # Print vertex coordinates
    print("Hexagon Vertices (x, y):")
    for i, vertex in enumerate(pixel_vertices):
        print(f"Vertex {i}: ({vertex[0]}, {vertex[1]})")
    
    # If rotation is requested, we need to determine which edge should be at the bottom
    if rotate:
        # For a flat-bottom hexagon, we need to find the bottom edge
        # A flat-bottom hexagon should have two vertices with similar y-coordinates at the bottom
        
        # First, sort vertices by y-coordinate (descending)
        vertices_by_y = sorted(enumerate(pixel_vertices), key=lambda x: x[1][1], reverse=True)
        
        # Get the two vertices with the largest y-coordinates (lowest on screen)
        bottom_vertices_indices = [vertices_by_y[0][0], vertices_by_y[1][0]]
        
        # Sort these two vertices by x-coordinate
        bottom_vertices_indices.sort(key=lambda idx: pixel_vertices[idx][0])
        
        # Get the coordinates of the bottom vertices
        bottom_left_idx = bottom_vertices_indices[0]
        bottom_right_idx = bottom_vertices_indices[1]
        
        bottom_left = pixel_vertices[bottom_left_idx]
        bottom_right = pixel_vertices[bottom_right_idx]
        
        # Draw the bottom edge in a different color
        draw = ImageDraw.Draw(unrotated_image)
        draw.line([bottom_left, bottom_right], fill="cyan", width=5)
        unrotated_image.save(f"{h3_index}_bottom_edge.png")
        print(f"Image with bottom edge highlighted saved to {h3_index}_bottom_edge.png")
        
        # Calculate the angle of the bottom edge with the horizontal
        dx = bottom_right[0] - bottom_left[0]
        dy = bottom_right[1] - bottom_left[1]
        edge_angle = math.degrees(math.atan2(dy, dx))
        
        print(f"\nBottom edge: Vertex {bottom_left_idx} to Vertex {bottom_right_idx}")
        print(f"Bottom edge coordinates: ({bottom_left[0]}, {bottom_left[1]}) to ({bottom_right[0]}, {bottom_right[1]})")
        print(f"Bottom edge angle with horizontal: {edge_angle:.2f} degrees")
        
        # Calculate rotation needed to make this edge horizontal
        rotation_angle = edge_angle  # Changed from -edge_angle to edge_angle
        print(f"Rotation angle needed: {rotation_angle:.2f} degrees")
        
        # Apply the rotation to make the bottom edge horizontal
        image, rotated_vertices = rotate_image_and_vertices(image, pixel_vertices, rotation_angle)
        
        # Draw all vertices on the rotated image
        draw = ImageDraw.Draw(image)
        
        # Draw circles at all vertices
        for i, vertex in enumerate(rotated_vertices):
            draw.ellipse((vertex[0]-radius, vertex[1]-radius, vertex[0]+radius, vertex[1]+radius), fill=colors[i % len(colors)])
        
        # Draw text labels with coordinates
        for i, vertex in enumerate(rotated_vertices):
            draw.text((vertex[0]+radius, vertex[1]-radius), f"{i}: ({vertex[0]}, {vertex[1]})", fill=colors[i % len(colors)], font=font)
        
        # Draw lines connecting the vertices in order
        for i in range(len(rotated_vertices)):
            next_i = (i + 1) % len(rotated_vertices)
            draw.line([rotated_vertices[i], rotated_vertices[next_i]], fill="white", width=2)
        
        # Find the bottom edge in the rotated image
        vertices_by_y = sorted(enumerate(rotated_vertices), key=lambda x: x[1][1], reverse=True)
        bottom_vertices_indices = [vertices_by_y[0][0], vertices_by_y[1][0]]
        bottom_vertices_indices.sort(key=lambda idx: rotated_vertices[idx][0])
        
        bottom_left_idx = bottom_vertices_indices[0]
        bottom_right_idx = bottom_vertices_indices[1]
        
        bottom_left = rotated_vertices[bottom_left_idx]
        bottom_right = rotated_vertices[bottom_right_idx]
        
        # Draw the bottom edge in the rotated image
        draw.line([bottom_left, bottom_right], fill="cyan", width=5)
        
        # Calculate the angle of the bottom edge after rotation
        dx = bottom_right[0] - bottom_left[0]
        dy = bottom_right[1] - bottom_left[1]
        edge_angle_after = math.degrees(math.atan2(dy, dx))
        
        print(f"\nAfter rotation:")
        print(f"Bottom edge: Vertex {bottom_left_idx} to Vertex {bottom_right_idx}")
        print(f"Bottom edge coordinates: ({bottom_left[0]}, {bottom_left[1]}) to ({bottom_right[0]}, {bottom_right[1]})")
        print(f"Bottom edge angle with horizontal: {edge_angle_after:.2f} degrees")
        
        # Save the rotated image with vertices
        image.save(f"{h3_index}_rotated.png")
        print(f"Rotated image saved to {h3_index}_rotated.png")
        
        # Update the pixel vertices to the rotated ones
        pixel_vertices = rotated_vertices
        
        # Now we need to crop and scale the image to make the hexagon fit perfectly
        # Find the leftmost and rightmost vertices
        leftmost_x = min(v[0] for v in pixel_vertices)
        rightmost_x = max(v[0] for v in pixel_vertices)
        topmost_y = min(v[1] for v in pixel_vertices)
        bottommost_y = max(v[1] for v in pixel_vertices)
        
        # Calculate the current width and height of the hexagon
        current_width = rightmost_x - leftmost_x
        current_height = bottommost_y - topmost_y
        
        # Calculate scaling factor to make the width exactly 1024 pixels
        scaling_factor = 1024 / current_width
        
        # Calculate new dimensions for the image
        new_width = int(image.width * scaling_factor)
        new_height = int(image.height * scaling_factor)
        
        # Calculate the center of the hexagon
        hex_center_x = (leftmost_x + rightmost_x) / 2
        hex_center_y = (topmost_y + bottommost_y) / 2
        
        # Calculate the crop box to center the hexagon
        crop_left = int(hex_center_x - (CANVAS_SIZE / 2 / scaling_factor))
        crop_top = int(hex_center_y - (CANVAS_SIZE / 2 / scaling_factor))
        crop_right = int(hex_center_x + (CANVAS_SIZE / 2 / scaling_factor))
        crop_bottom = int(hex_center_y + (CANVAS_SIZE / 2 / scaling_factor))
        
        # Ensure crop box is within image bounds
        crop_left = max(0, crop_left)
        crop_top = max(0, crop_top)
        crop_right = min(image.width, crop_right)
        crop_bottom = min(image.height, crop_bottom)
        
        # Crop the image
        cropped_image = image.crop((crop_left, crop_top, crop_right, crop_bottom))
        
        # Resize to 1024x1024
        final_image = cropped_image.resize((CANVAS_SIZE, CANVAS_SIZE), Image.LANCZOS)
        
        # Calculate the new vertex positions after cropping and scaling
        final_vertices = []
        for x, y in pixel_vertices:
            new_x = (x - crop_left) * scaling_factor
            new_y = (y - crop_top) * scaling_factor
            final_vertices.append((new_x, new_y))
        
        # Draw the final vertices for verification
        draw = ImageDraw.Draw(final_image)
        
        # Draw circles at all vertices
        for i, vertex in enumerate(final_vertices):
            draw.ellipse((vertex[0]-radius, vertex[1]-radius, vertex[0]+radius, vertex[1]+radius), fill=colors[i % len(colors)])
        
        # Draw text labels with coordinates
        for i, vertex in enumerate(final_vertices):
            draw.text((vertex[0]+radius, vertex[1]-radius), f"{i}: ({int(vertex[0])}, {int(vertex[1])})", fill=colors[i % len(colors)], font=font)
        
        # Draw lines connecting the vertices in order
        for i in range(len(final_vertices)):
            next_i = (i + 1) % len(final_vertices)
            draw.line([final_vertices[i], final_vertices[next_i]], fill="white", width=2)
        
        # Save the final image
        final_image.save(f"{h3_index}_final.png")
        print(f"Final image saved to {h3_index}_final.png")
        
        # Print the final vertex coordinates
        print("\nFinal Hexagon Vertices (x, y):")
        for i, vertex in enumerate(final_vertices):
            print(f"Vertex {i}: ({int(vertex[0])}, {int(vertex[1])})")
        
        # Update the image and vertices
        image = final_image
        pixel_vertices = final_vertices
    
    return image, pixel_vertices


def main():
    """Main function."""
    args = parse_arguments()
    
    try:
        # Create the map image
        img, vertices = create_hexagon_map(args.h3_index, args.zoom, not args.no_rotate)
        
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
