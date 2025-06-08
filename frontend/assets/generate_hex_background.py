#!/usr/bin/env python3
"""
Generate a hexagon background image for HexGlobe tiles.
Creates a 1024x1024 PNG with a flat-bottom hexagon in the center,
making the hexagon as large as possible with transparent background.
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

def generate_hex_background(output_path, size=1024, border_width=2, border_color=(50, 50, 50, 255), 
                           fill_color=(255, 255, 255, 255), add_text=True, text_color=(200, 200, 200, 128)):
    """
    Generate a flat-bottom hexagon background image.
    
    Args:
        output_path: Path to save the output PNG file
        size: Size of the square image (width and height)
        border_width: Width of the hexagon border in pixels
        border_color: RGBA color tuple for the border
        fill_color: RGBA color tuple for the hexagon fill
        add_text: Whether to add the "HexGlobe" text in the center
        text_color: RGBA color tuple for the text (faint grey by default)
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
    
    print(f"Image size: {size}x{size}")
    print(f"Center point: ({center_x}, {center_y})")
    print(f"Radius: {radius}")
    print("\nHexagon vertices:")
    
    # For a flat-bottom hexagon, we need these specific angles
    # 0° is to the right, and we go clockwise
    angles = [0, 60, 120, 180, 240, 300]  # in degrees
    
    # Calculate the six vertices of the hexagon
    points = []
    for i, angle in enumerate(angles):
        # Convert angle to radians
        rad = math.radians(angle)
        # Calculate the point
        x = center_x + radius * math.cos(rad)
        y = center_y + radius * math.sin(rad)
        points.append((x, y))
        print(f"Vertex {i+1} (angle {angle}°): ({x:.1f}, {y:.1f})")
    
    # Draw the hexagon with border
    if border_width > 0:
        draw.polygon(points, outline=border_color, fill=fill_color, width=border_width)
    else:
        draw.polygon(points, fill=fill_color)
    
    # Add "HexGlobe" text in the center if requested
    if add_text:
        try:
            # Try to load a system font
            font_size = int(size / 10)  # Adjust font size based on image size
            try:
                font = ImageFont.truetype("Arial", font_size)
            except IOError:
                # Fallback to default font if Arial is not available
                font = ImageFont.load_default()
                font_size = int(size / 15)  # Default font might be smaller
                
            text = "HexGlobe"
            # Get text size to center it properly
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Draw the text in the center
            text_position = (center_x - text_width / 2, center_y - text_height / 2)
            draw.text(text_position, text, font=font, fill=text_color)
        except Exception as e:
            print(f"Warning: Could not add text: {e}")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the image
    img.save(output_path)
    print(f"\nHexagon background image saved to {output_path}")
    
    return img

if __name__ == "__main__":
    # Create the assets directory if it doesn't exist
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # Generate a version with black border, light grey fill, and darker text
    custom_path = os.path.join(output_dir, "hex_map_placeholder.png")
    light_grey = (220, 220, 220, 255)  # Light grey fill
    darker_text = (150, 150, 150, 255)  # Darker text color
    generate_hex_background(
        custom_path,
        border_width=5,
        border_color=(0, 0, 0, 255),  # Black border
        fill_color=light_grey,
        text_color=darker_text
    )
