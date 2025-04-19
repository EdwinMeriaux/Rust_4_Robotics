def bresenham_with_obstacles(x0, y0, x1, y1, grid):
    """
    Bresenham's line algorithm with obstacle detection.
    
    :param x0, y0: Starting point
    :param x1, y1: Ending point
    :param grid: 2D list where 0 = free, 1 = blocked
    :return: List of visible points along the line
    """
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        if grid[y0][x0] == 1:  # Check for obstacle
            break  
        points.append((x0, y0))
        
        if x0 == x1 and y0 == y1:  # If end point is reached
            break
        
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

    return points

grid = [
    [0, 0, 0, 0, 0],
    [0, 1, 1, 1, 0],
    [0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0]
]

start = (0, 1)
end = (3, 4)

print(bresenham_with_obstacles(start[0], start[1], end[0], end[1], grid))
