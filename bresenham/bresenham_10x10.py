import json

import numpy as np 

def bresenham(p1, p2):
    """
    Compute Bresenham's line between two points.
    Returns a list of (x, y) points along the line.
    """
    x1, y1 = p1
    x2, y2 = p2

    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        points.append((x1, y1))  # Store the point
        if x1 == x2 and y1 == y2:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

    return points

def build_visibility_dict(grid):
    """
    Create a dictionary mapping each free cell to all visible cells.
    Visibility is blocked if any point on the Bresenham path is an obstacle.
    """
    grid_size = len(grid)
    visibility_dict = {}

    for y1 in range(grid_size):
        for x1 in range(grid_size):
            p1 = (x1, y1)

            if grid[y1,x1] == 1:  # If the point is an obstacle, no visibility
                visibility_dict[str(p1)] = []

            else:

                visible_points = set()

                for y2 in range(grid_size):
                    for x2 in range(grid_size):
                        p2 = (x2, y2)

                        #if p1 == p2 or grid[y2][x2] == 1:  # Skip self and obstacles
                        #    continue

                        # Get Bresenham line
                        line = bresenham(p1, p2)

                        rows, cols = zip(*line)
                        values = np.array(grid[np.array(rows), np.array(cols)])
                        #values = [grid[row, col] for row, col in line]

                        indices = np.where(values == 1)[0]  # Get indices of 1

                        if len(indices) == 0:
                            visible_points = visible_points.union(set(line))
                        else:
                            visible_points = visible_points.union(set(line[0:indices[0]]))

                        # Fix: Ensure no obstacles block the path
                        #blocked = any(grid[y][x] == 1 for x, y in line[1:-1])  # Check all except endpoints

                        #if not blocked:  # If no obstacles, p2 is visible
                        #    visible_points.add(p2)

                visibility_dict[str(p1)] = list(visible_points) # Store visible points for p1

    return visibility_dict

# Example 10x10 grid (0 = free, 1 = obstacle)
grid = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

grid = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0]
    ]

grid = np.matrix(grid)

# Generate the visibility dictionary
visibility_dict = build_visibility_dict(grid)

# Save to JSON file
with open("data.json", "w") as file:
    json.dump(visibility_dict, file, indent=4)
print()
# Test functions
def test_bresenham():
    """
    Test Bresenham's algorithm.
    """
    print("Testing Bresenham's algorithm...")
    p1 = (0, 0)
    p2 = (3, 3)
    line = bresenham(p1, p2)
    print(f"Line from {p1} to {p2}: {line}")  # Expected: [(0, 0), (1, 1), (2, 2), (3, 3)]

def test_visibility():
    """
    Test visibility calculation.
    """
    print("Testing visibility calculation...")
    test_grid = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0]
    ]
    visibility_dict = build_visibility_dict(test_grid)
    print(f"Visibility for (0, 0): {visibility_dict['(0, 0)']}")  # Expected: {(1, 0), (0, 1)}
    print(f"Visibility for (1, 1): {visibility_dict['(1, 1)']}")  # Expected: set()
    print(f"Visibility for (2, 2): {visibility_dict['(2, 2)']}")  # Expected: {(1, 2), (2, 1)}

# Run tests
if __name__ == "__main__":
    test_bresenham()
    test_visibility()
