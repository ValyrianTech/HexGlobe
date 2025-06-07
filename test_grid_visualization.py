#!/usr/bin/env python3
"""
Simple test script to visualize the hexagon grid from the grid endpoint.
"""
import sys
import requests
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import RegularPolygon
import matplotlib.colors as mcolors

def fetch_grid_data(tile_id, width=5, height=5):
    """Fetch grid data from the API endpoint."""
    url = f"http://127.0.0.1:8000/api/tiles/{tile_id}/grid"
    params = {
        "width": width,
        "height": height
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching grid data: {e}")
        sys.exit(1)

def verify_grid_positions(grid_data):
    """Verify if specific grid positions have the expected tile IDs."""
    grid_dict = grid_data["grid"]
    
    # Convert string keys back to tuple coordinates
    grid = {}
    for key, value in grid_dict.items():
        row, col = map(int, key.split(','))
        grid[(row, col)] = value
    
    # Expected neighbors at specific positions as provided by the user
    expected_positions = {
        # Position: Expected ID
        (0, 0): "8a194da9a74ffff",  # Center
        (-1, 0): "8a194da9a297fff",  # bottom_middle
        (-1, -1): "8a194da9a667fff",  # bottom_left
        (0, -1): "8a194da9a75ffff",  # top_left
        (1, 0): "8a194da9a747fff",  # top_middle
        (0, 1): "8a194da9a76ffff",  # top_right
        (-1, 1): "8a194da9a2b7fff",  # bottom_right
        
        # Additional positions from (0,0) to (4,4)
        # Fill in the expected IDs manually after running the script once
        (-2, -2): "8a194da9a64ffff",  # Fill in expected ID
        (-2, -1): "8a194da9a66ffff",  # Fill in expected ID
        (-2, 0): "8a194da9a29ffff",  # Fill in expected ID
        (-2, 1): "8a194da9a287fff",  # Fill in expected ID
        (-2, 2): "8a194da9a2affff",  # Fill in expected ID
        
        (-1, -2): "8a194da9a647fff",  # Fill in expected ID
        (-1, 2): "8a194da9a2a7fff",  # Fill in expected ID
        
        (0, -2): "8a194da9a677fff",  # Fill in expected ID
        (0, 2): "8a194da9a39ffff",  # Fill in expected ID
        
        (1, -2): "8a194da9a62ffff",  # Fill in expected ID
        (1, -1): "8a194da9a757fff",  # Fill in expected ID
        (1, 1): "8a194da9a767fff",  # Fill in expected ID
        (1, 2): "8a194da9a397fff",  # Fill in expected ID
        
        (2, -2): "8a194da9a627fff",  # Fill in expected ID
        (2, -1): "8a194da9a70ffff",  # Fill in expected ID
        (2, 0): "8a194da9a777fff",  # Fill in expected ID
        (2, 1): "8a194da9a0dffff",  # Fill in expected ID
        (2, 2): "8a194da9a0cffff",  # Fill in expected ID
    }
    
    print("\nChecking grid positions:")
    print("------------------------")
    
    all_match = True
    
    # First, print the actual grid for reference using center-based coordinates
    print("\nActual grid contents (center-based coordinates):")
    print("-------------------------------------------")
    
    # Get the bounds of the grid
    bounds = grid_data.get("bounds", {})
    min_row = bounds.get("min_row", -2)
    max_row = bounds.get("max_row", 2)
    min_col = bounds.get("min_col", -2)
    max_col = bounds.get("max_col", 2)
    
    for row in range(min_row, max_row + 1):
        row_values = []
        for col in range(min_col, max_col + 1):
            if (row, col) in grid:
                row_values.append(f"({row},{col}): {grid[(row, col)]}")
        if row_values:
            print(", ".join(row_values))
    
    print("\nPosition verification:")
    print("--------------------")
    for (row, col), expected_id in expected_positions.items():
        if (row, col) in grid:
            actual_id = grid[(row, col)]
            
            # Skip empty expected IDs (to be filled in manually)
            if not expected_id:
                print(f"? Position ({row}, {col}): Expected=<not specified>, Actual={actual_id}")
                continue
                
            match = actual_id == expected_id
            status = "✓" if match else "✗"
            print(f"{status} Position ({row}, {col}): Expected={expected_id}, Actual={actual_id}")
            if not match:
                all_match = False
        else:
            print(f"✗ Position ({row}, {col}) is out of grid bounds or empty")
            all_match = False
    
    # Also print the grid in a structured format for easier visualization
    print("\nGrid Contents (Visual Format):")
    print("-----------------------------")
    
    # Print the grid in a structured format
    for row in range(max_row, min_row - 1, -1):  # Print top to bottom
        # Add indentation for odd rows to represent hexagonal grid
        indent = "  " if row % 2 == 0 else ""
        row_str = f"{row:2d} | {indent}"
        
        for col in range(min_col, max_col + 1):
            pos = (row, col)
            tile_id = grid.get(pos)
            if tile_id:
                # Show abbreviated ID for readability
                short_id = tile_id[-7:-3]
                row_str += f"{short_id} "
            else:
                row_str += ".... "
        
        print(row_str)
    
    # Print column headers
    col_header = "   |  "
    for col in range(min_col, max_col + 1):
        col_header += f"{col:2d}   "
    print(col_header)
    
    print("\nGrid position check:", "PASSED" if all_match else "FAILED")
    return all_match

def draw_hexagon_grid(grid_data):
    """Draw a hexagon grid with IDs in the center of each tile."""
    grid_dict = grid_data["grid"]
    pentagon_positions = grid_data.get("pentagon_positions", [])
    
    # Convert string keys back to tuple coordinates
    grid = {}
    for key, value in grid_dict.items():
        row, col = map(int, key.split(','))
        grid[(row, col)] = value
    
    # Get the bounds of the grid
    bounds = grid_data.get("bounds", {})
    min_row = bounds.get("min_row", -2)
    max_row = bounds.get("max_row", 2)
    min_col = bounds.get("min_col", -2)
    max_col = bounds.get("max_col", 2)
    
    # Calculate grid dimensions
    height = max_row - min_row + 1
    width = max_col - min_col + 1
    
    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(15, 12))
    ax.set_aspect('equal')
    
    # Define colors
    normal_color = 'lightblue'
    pentagon_color = 'salmon'
    center_color = 'lightgreen'
    
    # Size of hexagons
    hex_size = 1.0
    
    # Horizontal and vertical spacing
    horiz_spacing = 1.5 * hex_size
    vert_spacing = np.sqrt(3) * hex_size
    
    # Track which positions have pentagons
    pentagon_coords = {tuple(pos) for pos in pentagon_positions}
    
    # Draw hexagons
    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col + 1):
            pos = (row, col)
            tile_id = grid.get(pos)
            
            if tile_id is None:
                continue
                
            # Calculate position (offset every other row for flat-bottom hexagons)
            # Convert from logical coordinates to screen coordinates
            x = (col - min_col) * horiz_spacing
            y = (row - min_row) * vert_spacing
            if col % 2 == 1:
                y += vert_spacing / 2
                
            # Determine color based on type
            if row == 0 and col == 0:  # Center tile at (0,0)
                color = center_color
            elif pos in pentagon_coords:
                color = pentagon_color
            else:
                color = normal_color
                
            # Create and add the hexagon to the plot - orientation=np.pi/6 for flat bottom
            hexagon = RegularPolygon((x, y), numVertices=6, radius=hex_size,
                                    orientation=np.pi/6, facecolor=color, 
                                    edgecolor='black', alpha=0.7)
            ax.add_patch(hexagon)
            
            # Add the full ID text
            # Use smaller font and full ID
            ax.text(x, y, tile_id, ha='center', va='center', fontsize=6)
            
            # Add logical coordinates for debugging
            ax.text(x, y + 0.3, f"({row},{col})", ha='center', va='center', fontsize=6, color='red')
    
    # Set axis limits with some padding
    ax.set_xlim(-1, width * horiz_spacing + 1)
    ax.set_ylim(-1, height * vert_spacing + 1)
    
    # Remove axis ticks and labels
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add a title
    center_id = grid_data["center_tile_id"]
    ax.set_title(f"Hexagon Grid for Tile: {center_id}")
    
    # Add a legend
    import matplotlib.patches as mpatches
    center_patch = mpatches.Patch(color=center_color, label='Center Tile')
    normal_patch = mpatches.Patch(color=normal_color, label='Regular Hexagon')
    pentagon_patch = mpatches.Patch(color=pentagon_color, label='Pentagon')
    ax.legend(handles=[center_patch, normal_patch, pentagon_patch], loc='upper right')
    
    # Show the plot
    plt.tight_layout()
    plt.savefig('grid_visualization.png')
    print("Visualization saved as 'grid_visualization.png'")
    plt.show()

def main():
    """Main function to fetch and visualize the grid."""
    # Default tile ID and grid dimensions
    tile_id = "8a194da9a74ffff"
    width = 5
    height = 5
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        tile_id = sys.argv[1]
    if len(sys.argv) > 2:
        width = int(sys.argv[2])
    if len(sys.argv) > 3:
        height = int(sys.argv[3])
    
    print(f"Fetching grid for tile: {tile_id}, width: {width}, height: {height}")
    grid_data = fetch_grid_data(tile_id, width, height)
    print("Grid data fetched successfully")
    
    # Verify grid positions
    verify_grid_positions(grid_data)
    
    print("Drawing hexagon grid...")
    draw_hexagon_grid(grid_data)

if __name__ == "__main__":
    main()
