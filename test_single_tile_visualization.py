#!/usr/bin/env python3
"""
Test script to visualize a single hexagon tile and its neighbors.

Usage:
    python test_single_tile_visualization.py [tile_id]
    
Example:
    python test_single_tile_visualization.py 8a194da9a74ffff
"""
import sys
import requests
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import RegularPolygon
import matplotlib.colors as mcolors

def fetch_tile_data(tile_id):
    """Fetch tile data from the API endpoint."""
    url = f"http://127.0.0.1:8000/api/tiles/{tile_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tile data: {e}")
        sys.exit(1)

def draw_single_tile(tile_data):
    """Draw a single tile and its neighbors."""
    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_aspect('equal')
    
    # Define colors
    center_color = 'lightgreen'
    neighbor_color = 'lightblue'
    pentagon_color = 'salmon'
    
    # Size of hexagons
    hex_size = 1.0
    
    # Get neighbor data
    neighbor_ids = tile_data.get("neighbor_ids", {})
    
    # Define the positions for each neighbor type in a flat-bottom hexagon layout
    # Using integer coordinates for easier grid mapping
    # For a flat-bottom hexagon, we use an axial coordinate system
    # where (q,r) represents position with q = column axis and r = row axis
    position_coords = {
        "center": (0, 0),        # Center position
        "top_middle": (0, -1),   # North
        "top_left": (-1, 0),     # Northwest
        "top_right": (1, -1),    # Northeast
        "bottom_middle": (0, 1), # South
        "bottom_left": (-1, 1),  # Southwest
        "bottom_right": (1, 0)   # Southeast
    }
    
    # Draw the center tile
    center_id = tile_data["id"]
    center_x, center_y = 0, 0
    
    # Create and add the center hexagon
    center_hexagon = RegularPolygon((center_x, center_y), numVertices=6, radius=hex_size,
                                   orientation=np.pi/6, facecolor=center_color, 
                                   edgecolor='black', alpha=0.7)
    ax.add_patch(center_hexagon)
    
    # Add the center tile ID text
    ax.text(center_x, center_y, center_id, ha='center', va='center', fontsize=8)
    ax.text(center_x, center_y + 0.3, "(0,0)", ha='center', va='center', fontsize=8, color='red')
    
    # Draw neighbor tiles
    for position, neighbor_id in neighbor_ids.items():
        # Skip if this is a pentagon marker
        if neighbor_id == "pentagon":
            continue
            
        # Get the position coordinates
        if position in position_coords:
            q, r = position_coords[position]
            
            # Calculate the x, y position for axial coordinates
            # Convert axial coordinates (q,r) to pixel coordinates (x,y)
            # For flat-topped hexagons with y-axis inverted to put "top" neighbors at the top
            x = hex_size * (1.5 * q)
            y = -hex_size * (np.sqrt(3)/2 * q + np.sqrt(3) * r)  # Invert y-axis
            
            # Create and add the neighbor hexagon
            neighbor_hexagon = RegularPolygon((x, y), numVertices=6, radius=hex_size,
                                            orientation=np.pi/6, facecolor=neighbor_color, 
                                            edgecolor='black', alpha=0.7)
            ax.add_patch(neighbor_hexagon)
            
            # Add the neighbor tile ID text
            ax.text(x, y, neighbor_id, ha='center', va='center', fontsize=8)
            ax.text(x, y + 0.3, f"({q},{r})", ha='center', va='center', fontsize=8, color='red')
            
            # Add position label
            ax.text(x, y - 0.3, position, ha='center', va='center', fontsize=8, color='blue')
    
    # Set axis limits with some padding
    ax.set_xlim(-3 * hex_size, 3 * hex_size)
    ax.set_ylim(-3 * hex_size, 3 * hex_size)
    
    # Remove axis ticks and labels
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add a title
    ax.set_title(f"Single Tile Visualization: {center_id}")
    
    # Add a legend
    import matplotlib.patches as mpatches
    center_patch = mpatches.Patch(color=center_color, label='Center Tile')
    neighbor_patch = mpatches.Patch(color=neighbor_color, label='Neighbor Tile')
    ax.legend(handles=[center_patch, neighbor_patch], loc='upper right')
    
    # Add tile information
    info_text = [
        f"Tile ID: {center_id}",
        f"Parent ID: {tile_data.get('parent_id', 'N/A')}",
        f"Children: {len(tile_data.get('children_ids', []))}",
        f"Neighbors: {len(neighbor_ids)}"
    ]
    
    # Add visual properties
    visual_props = tile_data.get("visual_properties", {})
    if visual_props:
        info_text.append("\nVisual Properties:")
        for prop, value in visual_props.items():
            info_text.append(f"  {prop}: {value}")
    
    # Add resolution IDs
    resolution_ids = tile_data.get("resolution_ids", {})
    if resolution_ids:
        info_text.append("\nResolution IDs:")
        for res, res_id in sorted(resolution_ids.items(), key=lambda x: int(x[0])):
            info_text.append(f"  Res {res}: {res_id}")
    
    # Add the information text box
    plt.figtext(0.02, 0.02, "\n".join(info_text), fontsize=8, 
                bbox=dict(facecolor='white', alpha=0.8, boxstyle='round'))
    
    # Show the plot
    plt.tight_layout()
    plt.savefig('single_tile_visualization.png')
    print("Visualization saved as 'single_tile_visualization.png'")
    plt.show()

def main():
    """Main function to fetch and visualize a single tile."""
    # Default tile ID
    tile_id = "8a194da9a74ffff"
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        tile_id = sys.argv[1]
    
    print(f"Fetching data for tile: {tile_id}")
    tile_data = fetch_tile_data(tile_id)
    print("Tile data fetched successfully")
    
    print("Drawing single tile visualization...")
    draw_single_tile(tile_data)
    
    # Return the tile_id for testing purposes
    return tile_id

if __name__ == "__main__":
    main()
