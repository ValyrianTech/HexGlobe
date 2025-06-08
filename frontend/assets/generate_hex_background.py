#!/usr/bin/env python3
"""
Generate a hexagon background image for HexGlobe tiles.
Creates a 1024x1024 PNG with a flat-bottom hexagon in the center,
making the hexagon as large as possible with transparent background.
"""

import os
import math
from PIL import Image, ImageDraw

def generate_hex_background(output_path, size=1024, border_width=2, border_color=(50, 50, 50, 255), 
                           fill_color=(255, 255, 255, 255)):
    """
    Generate a flat-bottom hexagon background image.
    
    Args:
        output_path: Path to save the output PNG file
        size: Size of the square image (width and height)
        border_width: Width of the hexagon border in pixels
        border_color: RGBA color tuple for the border
        fill_color: RGBA color tuple for the hexagon fill
    """
    # Create a transparent image
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # For a flat-bottom hexagon in a square:
    # - Width is limited by the image width
    # - Height is determined by the width
    
    # Calculate the center of the image
    center_x = size / 2
    center_y = size / 2
    
    # For a regular hexagon, the distance from center to any vertex is the same
    # We'll use the maximum radius that fits within the image
    radius = size / 2
    
    # For a flat-bottom hexagon, we need these specific angles
    # 0° is to the right, and we go clockwise
    angles = [0, 60, 120, 180, 240, 300]  # in degrees
    
    # Calculate the six vertices of the hexagon
    points = []
    for angle in angles:
        # Convert angle to radians
        rad = math.radians(angle)
        # Calculate the point
        x = center_x + radius * math.cos(rad)
        y = center_y + radius * math.sin(rad)
        points.append((x, y))
    
    # Draw the hexagon with border
    if border_width > 0:
        draw.polygon(points, outline=border_color, fill=fill_color, width=border_width)
    else:
        draw.polygon(points, fill=fill_color)
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the image
    img.save(output_path)
    print(f"Hexagon background image saved to {output_path}")
    
    return img

if __name__ == "__main__":
    # Create the assets directory if it doesn't exist
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "hex_background.png")
    
    # Generate the default hexagon background
    generate_hex_background(output_path)
    
    # Generate a subtle version with custom properties
    subtle_path = os.path.join(output_dir, "subtle_hex_background.png")
    generate_hex_background(
        subtle_path, 
        border_width=2, 
        border_color=(100, 100, 120, 255),
        fill_color=(245, 245, 250, 180)  # Semi-transparent fill
    )
