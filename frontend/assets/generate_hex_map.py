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
from PIL import Image, ImageDraw, ImageFont
from staticmap import StaticMap, Line
import numpy as np
import json
import sys

# Import the get_hex_map_path helper function from the tile module
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend"))
try:
    from hexglobe.models.tile import get_hex_map_path
except ImportError:
    print("Warning: Could not import get_hex_map_path from tile module. Using default path.")
    def get_hex_map_path(h3_index):
        return f"{h3_index}.png"

# Constants for the image rendering
CANVAS_SIZE = 1024
HEXAGON_BORDER_WIDTH = 5
HEXAGON_BORDER_COLOR = "#00FF00"  # Green border for visibility
OUTER_HEXAGON_COLOR = "#FF0000"   # Red for outer hexagon
INNER_HEXAGON_COLOR = "#0000FF"   # Blue for inner hexagon
# Use percentage-based offsets to match frontend scaling
OUTER_OFFSET_PERCENT = 0.05       # 5% offset outward
INNER_OFFSET_PERCENT = 0.05       # 5% offset inward
# Constants for reference points
REFERENCE_DOT_COLOR = "#000000"   # Black dots for reference points
REFERENCE_DOT_RADIUS = 20         # Size of the reference dots

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate map images for HexGlobe hexagons.')
    parser.add_argument('--h3_index', required=True, help='H3 index of the tile')
    parser.add_argument('--output', default=None, help='Output file path (default: uses get_hex_map_path from tile module)')
    parser.add_argument('--zoom', type=int, default=None, 
                        help='OpenStreetMap zoom level (1-19, default: auto-calculated)')
    parser.add_argument('--vertices', action='store_true',
                        help='Output the pixel coordinates of the hexagon vertices')
    parser.add_argument('--no-rotate', action='store_true',
                        help='Skip rotation to flat-bottom orientation')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode (save intermediate images and print debug info)')
    parser.add_argument('--no-vertical-adjust', action='store_true',
                        help='Skip vertical adjustment')
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


def offset_edge(p1, p2, distance):
    """
    Offset an edge by a perpendicular distance.
    
    Args:
        p1: (x, y) coordinates of first point
        p2: (x, y) coordinates of second point
        distance: Distance to offset (positive = outward, negative = inward)
        
    Returns:
        Two new points representing the offset edge
    """
    # Calculate the vector of the edge
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    
    # Calculate the length of the edge
    length = math.sqrt(dx*dx + dy*dy)
    
    # Normalize the vector
    if length > 0:
        dx /= length
        dy /= length
    
    # Calculate the perpendicular vector (rotate 90 degrees)
    perpx = -dy
    perpy = dx
    
    # Offset the points
    new_p1 = (p1[0] + perpx * distance, p1[1] + perpy * distance)
    new_p2 = (p2[0] + perpx * distance, p2[1] + perpy * distance)
    
    return new_p1, new_p2


def create_offset_polygon(vertices, distance):
    """
    Create a new polygon by offsetting each edge of the original polygon.
    
    Args:
        vertices: List of (x, y) vertex coordinates
        distance: Distance to offset edges (positive = outward, negative = inward)
        
    Returns:
        List of (x, y) vertex coordinates for the offset polygon
    """
    num_vertices = len(vertices)
    offset_edges = []
    
    # Offset each edge
    for i in range(num_vertices):
        next_i = (i + 1) % num_vertices
        p1 = vertices[i]
        p2 = vertices[next_i]
        
        new_p1, new_p2 = offset_edge(p1, p2, distance)
        offset_edges.append((new_p1, new_p2))
    
    # Find the intersection points of adjacent offset edges
    offset_vertices = []
    for i in range(num_vertices):
        prev_i = (i - 1) % num_vertices
        
        line1_p1, line1_p2 = offset_edges[prev_i]
        line2_p1, line2_p2 = offset_edges[i]
        
        # Calculate intersection
        try:
            intersection = line_intersection(line1_p1, line1_p2, line2_p1, line2_p2)
            offset_vertices.append(intersection)
        except Exception:
            # If lines are parallel or coincident, use the endpoint
            offset_vertices.append(line2_p1)
    
    return offset_vertices


def line_intersection(line1_p1, line1_p2, line2_p1, line2_p2):
    """
    Find the intersection point of two lines.
    
    Args:
        line1_p1, line1_p2: Two points defining the first line
        line2_p1, line2_p2: Two points defining the second line
        
    Returns:
        (x, y) coordinates of the intersection point
    """
    # Convert to the form Ax + By = C
    a1 = line1_p2[1] - line1_p1[1]
    b1 = line1_p1[0] - line1_p2[0]
    c1 = a1 * line1_p1[0] + b1 * line1_p1[1]
    
    a2 = line2_p2[1] - line2_p1[1]
    b2 = line2_p1[0] - line2_p2[0]
    c2 = a2 * line2_p1[0] + b2 * line2_p1[1]
    
    determinant = a1 * b2 - a2 * b1
    
    if determinant == 0:
        # Lines are parallel or coincident
        raise Exception("Lines do not intersect")
    
    x = (b2 * c1 - b1 * c2) / determinant
    y = (a1 * c2 - a2 * c1) / determinant
    
    return (x, y)


def calculate_hexagon_vertices(center_x, center_y, size):
    """
    Calculate hexagon vertices using the same approach as the frontend.
    
    Args:
        center_x: X coordinate of the center
        center_y: Y coordinate of the center
        size: Size of the hexagon (distance from center to vertex)
        
    Returns:
        List of (x, y) vertex coordinates
    """
    vertices = []
    
    # Use the same approach as the frontend: start with angle 0 for flat-bottom orientation
    for i in range(6):
        angle = (math.pi / 3) * i  # No offset, start at 0
        x = center_x + size * math.cos(angle)
        y = center_y + size * math.sin(angle)
        vertices.append((x, y))
    
    return vertices


def scale_polygon(vertices, scale_factor, center=None):
    """
    Scale a polygon (list of vertices) by a given factor around a center point.
    
    Args:
        vertices: List of (x, y) vertex coordinates
        scale_factor: Factor to scale by (>1 for larger, <1 for smaller)
        center: (x, y) center point to scale around (if None, uses centroid)
        
    Returns:
        List of scaled (x, y) vertex coordinates
    """
    if center is None:
        # Calculate centroid if no center is provided
        center_x = sum(v[0] for v in vertices) / len(vertices)
        center_y = sum(v[1] for v in vertices) / len(vertices)
        center = (center_x, center_y)
    
    scaled_vertices = []
    for x, y in vertices:
        # Vector from center to vertex
        dx = x - center[0]
        dy = y - center[1]
        
        # Scale the vector
        scaled_x = center[0] + dx * scale_factor
        scaled_y = center[1] + dy * scale_factor
        
        scaled_vertices.append((scaled_x, scaled_y))
    
    return scaled_vertices


def apply_vertical_scaling_and_skew(image, pixel_vertices):
    """
    Apply vertical scaling and horizontal skew to the image to make the H3 hexagon match a perfect hexagon.
    
    Args:
        image: PIL Image object
        pixel_vertices: List of (x, y) tuples representing the hexagon vertices
    
    Returns:
        Adjusted PIL Image object
    """
    # Perfect hexagon reference points (flat-bottom orientation)
    perfect_hexagon = [
        (1024.0, 512.0),  # right middle
        (768.0, 955.4),   # bottom right
        (256.0, 955.4),   # bottom left
        (0.0, 512.0),     # left middle
        (256.0, 68.6),    # top left
        (768.0, 68.6)     # top right
    ]
    
    # Map the actual vertices to match the perfect hexagon order
    # pixel_vertices order: top-right, top-left, left, bottom-left, bottom-right, right
    # perfect_hexagon order: right, bottom-right, bottom-left, left, top-left, top-right
    vertex_mapping = {
        0: 5,  # top-right -> top-right
        1: 4,  # top-left -> top-left
        2: 3,  # left -> left
        3: 2,  # bottom-left -> bottom-left
        4: 1,  # bottom-right -> bottom-right
        5: 0,  # right -> right
    }
    
    # Reorder actual vertices to match perfect hexagon order
    mapped_vertices = [pixel_vertices[i] for i in range(len(pixel_vertices))]
    
    # Calculate vertical scaling factor
    # Get the average y-coordinate for top vertices
    actual_top_y_avg = (pixel_vertices[0][1] + pixel_vertices[1][1]) / 2
    perfect_top_y_avg = (perfect_hexagon[4][1] + perfect_hexagon[5][1]) / 2
    
    # Get the average y-coordinate for bottom vertices
    actual_bottom_y_avg = (pixel_vertices[3][1] + pixel_vertices[4][1]) / 2
    perfect_bottom_y_avg = (perfect_hexagon[1][1] + perfect_hexagon[2][1]) / 2
    
    # Calculate the vertical distance in both cases
    actual_vertical_distance = actual_bottom_y_avg - actual_top_y_avg
    perfect_vertical_distance = perfect_bottom_y_avg - perfect_top_y_avg
    
    # Calculate vertical scaling factor
    vertical_scale_factor = perfect_vertical_distance / actual_vertical_distance
    
    # For PIL's transform method, we need to invert the scaling factor
    applied_vertical_scale = 1 / vertical_scale_factor
    
    # Calculate horizontal skew factor
    # Get the x-offsets at the top
    actual_top_left_x = pixel_vertices[1][0]
    perfect_top_left_x = perfect_hexagon[4][0]
    actual_top_right_x = pixel_vertices[0][0]
    perfect_top_right_x = perfect_hexagon[5][0]
    
    # Get the x-offsets at the bottom
    actual_bottom_left_x = pixel_vertices[3][0]
    perfect_bottom_left_x = perfect_hexagon[2][0]
    actual_bottom_right_x = pixel_vertices[4][0]
    perfect_bottom_right_x = perfect_hexagon[1][0]
    
    # Calculate average offsets
    top_offset = ((perfect_top_left_x - actual_top_left_x) + (perfect_top_right_x - actual_top_right_x)) / 2
    bottom_offset = ((perfect_bottom_left_x - actual_bottom_left_x) + (perfect_bottom_right_x - actual_bottom_right_x)) / 2
    
    # Calculate vertical distance from center to top/bottom
    vertical_distance = CANVAS_SIZE / 2
    
    # Calculate skew factor
    skew_factor = (top_offset - bottom_offset) / (2 * vertical_distance)
    
    # Calculate centers for the transformations
    center_x = CANVAS_SIZE / 2
    center_y = CANVAS_SIZE / 2
    
    # First apply vertical scaling
    # Calculate the affine transformation matrix for vertical scaling
    scale_matrix = (
        1, 0, 0,
        0, applied_vertical_scale, (1 - applied_vertical_scale) * center_y
    )
    
    # Apply the vertical scaling transformation
    scaled_image = image.transform(
        (CANVAS_SIZE, CANVAS_SIZE),
        Image.AFFINE,
        scale_matrix,
        resample=Image.BICUBIC
    )
    
    # Then apply horizontal skew
    # Calculate the affine transformation matrix for horizontal skew
    # This shifts x based on y-position: x_new = x + (y - center_y) * skew_factor
    skew_matrix = (
        1, skew_factor, -skew_factor * center_y,
        0, 1, 0
    )
    
    # Apply the skew transformation
    final_image = scaled_image.transform(
        (CANVAS_SIZE, CANVAS_SIZE),
        Image.AFFINE,
        skew_matrix,
        resample=Image.BICUBIC
    )
    
    print(f"Applied vertical scaling with factor: {vertical_scale_factor:.4f} (applied as {applied_vertical_scale:.4f})")
    print(f"Applied horizontal skew with factor: {skew_factor:.6f}")
    
    return final_image


def create_hexagon_map(h3_index, zoom=None, rotate=True, debug=False, vertical_adjust=True):
    """
    Create a hexagon map image for the given H3 index.
    
    Args:
        h3_index: H3 index to create map for
        zoom: Zoom level (optional)
        rotate: Whether to rotate the image to align with the hexagon
        debug: Whether to enable debug mode
        vertical_adjust: Whether to apply vertical adjustment to match perfect hexagon
    
    Returns:
        PIL Image object and list of pixel vertices
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
    
    # Draw all vertices on the image with labels if debug is enabled
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(image)
    
    # Calculate the center of the hexagon
    center_x = sum(v[0] for v in pixel_vertices) / len(pixel_vertices)
    center_y = sum(v[1] for v in pixel_vertices) / len(pixel_vertices)
    center_point = (center_x, center_y)
    
    # Create outer and inner hexagons by scaling the original vertices
    # This preserves the correct orientation and alignment
    outer_vertices = scale_polygon(pixel_vertices, 1 + OUTER_OFFSET_PERCENT, center_point)
    inner_vertices = scale_polygon(pixel_vertices, 1 - INNER_OFFSET_PERCENT, center_point)
    
    # Draw the outer hexagon (red)
    for i in range(len(outer_vertices)):
        next_i = (i + 1) % len(outer_vertices)
        draw.line([outer_vertices[i], outer_vertices[next_i]], fill=OUTER_HEXAGON_COLOR, width=HEXAGON_BORDER_WIDTH)
    
    # Draw the inner hexagon (blue)
    for i in range(len(inner_vertices)):
        next_i = (i + 1) % len(inner_vertices)
        draw.line([inner_vertices[i], inner_vertices[next_i]], fill=INNER_HEXAGON_COLOR, width=HEXAGON_BORDER_WIDTH)
    
    # Draw the main hexagon (green) - use the original vertices
    for i in range(len(pixel_vertices)):
        next_i = (i + 1) % len(pixel_vertices)
        draw.line([pixel_vertices[i], pixel_vertices[next_i]], fill=HEXAGON_BORDER_COLOR, width=HEXAGON_BORDER_WIDTH)
    
    if debug:
        # Draw circles at all vertices
        colors = ["red", "orange", "yellow", "green", "blue", "purple"]
        radius = REFERENCE_DOT_RADIUS
        
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
    
    # Save the unrotated image for reference if debug is enabled
    unrotated_image = image.copy()
    if debug:
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
        
        bottom_left_idx = bottom_vertices_indices[0]
        bottom_right_idx = bottom_vertices_indices[1]
        
        bottom_left = pixel_vertices[bottom_left_idx]
        bottom_right = pixel_vertices[bottom_right_idx]
        
        # Draw the bottom edge in a different color if debug is enabled
        if debug:
            draw = ImageDraw.Draw(unrotated_image)
            draw.line([bottom_left, bottom_right], fill="cyan", width=5)
            unrotated_image.save(f"{h3_index}_bottom_edge.png")
            print(f"Image with bottom edge highlighted saved to {h3_index}_bottom_edge.png")
        
        # Calculate the angle of the bottom edge with the horizontal
        dx = bottom_right[0] - bottom_left[0]
        dy = bottom_right[1] - bottom_left[1]
        edge_angle = math.degrees(math.atan2(dy, dx))
        
        if debug:
            print(f"\nBottom edge: Vertex {bottom_left_idx} to Vertex {bottom_right_idx}")
            print(f"Bottom edge coordinates: ({bottom_left[0]}, {bottom_left[1]}) to ({bottom_right[0]}, {bottom_right[1]})")
            print(f"Bottom edge angle with horizontal: {edge_angle:.2f} degrees")
        
        # Calculate rotation needed to make this edge horizontal
        rotation_angle = edge_angle  # Changed from -edge_angle to edge_angle
        if debug:
            print(f"Rotation angle needed: {rotation_angle:.2f} degrees")
        
        # Apply the rotation to make the bottom edge horizontal
        image, rotated_vertices = rotate_image_and_vertices(image, pixel_vertices, rotation_angle)
        
        # Draw all vertices on the rotated image if debug is enabled
        if debug:
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
        
        # Draw the bottom edge in the rotated image if debug is enabled
        if debug:
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
        
        # Draw the final vertices for verification if debug is enabled
        if debug:
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
            
            # Save the final image with debug info
            final_image.save(f"{h3_index}_final.png")
            print(f"Final image saved to {h3_index}_final.png")
            
            # Print the final vertex coordinates
            print("\nFinal Hexagon Vertices (x, y):")
            for i, vertex in enumerate(final_vertices):
                print(f"Vertex {i}: ({int(vertex[0])}, {int(vertex[1])})")
        
        # Update the image and vertices
        image = final_image
        pixel_vertices = final_vertices
    
    # Apply vertical scaling and horizontal skew if enabled
    if vertical_adjust:
        image = apply_vertical_scaling_and_skew(image, pixel_vertices)
    
    return image, pixel_vertices


def save_final_image(image, output_path, debug=False):
    """
    Save the final image after adding reference dots at specific pixel coordinates.
    
    Args:
        image: PIL Image object
        output_path: Path to save the image to
        debug: Whether to enable debug mode
    """
    # Create a copy of the image to draw on
    final_image = image.copy()
    draw = ImageDraw.Draw(final_image)
    
    # Draw reference dots at specific pixel coordinates
    reference_points = [
        (1024.0, 512.0),  # Vertex 1 (angle 0°): right middle
        (768.0, 955.4),   # Vertex 2 (angle 60°): bottom right
        (256.0, 955.4),   # Vertex 3 (angle 120°): bottom left
        (0.0, 512.0),     # Vertex 4 (angle 180°): left middle
        (256.0, 68.6),    # Vertex 5 (angle 240°): top left
        (768.0, 68.6)     # Vertex 6 (angle 300°): top right
    ]
    
    # Draw each reference point
    for i, point in enumerate(reference_points):
        x, y = point
        # Draw a filled circle
        draw.ellipse(
            [(x - REFERENCE_DOT_RADIUS, y - REFERENCE_DOT_RADIUS), 
             (x + REFERENCE_DOT_RADIUS, y + REFERENCE_DOT_RADIUS)], 
            fill=REFERENCE_DOT_COLOR
        )
        
        # Add a label if in debug mode
        if debug:
            font = ImageFont.load_default()
            draw.text((x + REFERENCE_DOT_RADIUS + 5, y), f"V{i+1}", fill=REFERENCE_DOT_COLOR, font=font)
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Save the final image
    final_image.save(output_path)
    print(f"Map image saved to {output_path}")


def main():
    """Main function to parse arguments and create the hexagon map."""
    args = parse_arguments()
    
    # Create the hexagon map
    image, vertices = create_hexagon_map(args.h3_index, args.zoom, not args.no_rotate, args.debug, not args.no_vertical_adjust)
    
    # Determine the output path
    output_path = args.output
    if not output_path:
        try:
            # Try to import the get_hex_map_path function from the backend
            from hexglobe.models.tile import get_hex_map_path
            output_path = get_hex_map_path(args.h3_index)
            print(f"Using backend path: {output_path}")
        except ImportError:
            # Fall back to a default path if the import fails
            print("Could not import get_hex_map_path from backend, using default path")
            output_path = os.path.join(os.getcwd(), f"{args.h3_index}.png")
    
    # Save the final image with reference dots
    save_final_image(image, output_path, args.debug)
    
    # If vertices flag is set, print the pixel vertices
    if args.vertices:
        print("Pixel vertices:")
        for i, vertex in enumerate(vertices):
            print(f"Vertex {i+1}: {vertex}")


if __name__ == "__main__":
    exit(main())
