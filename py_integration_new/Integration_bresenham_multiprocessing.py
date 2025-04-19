import multiprocessing
import json
import numpy as np
#still need to fix json output
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

def agent(task_queue, visibility_queue, agent_id, grid):
    while True:
        task = task_queue.get()
        if task is None:  # Stop the agent if no more tasks
            break
        print(f"Agent {agent_id} processing task: {task}")
        
        visible_points = set()
        for point in task:
            x1, y1 = point
            p1 = (x1, y1)
            if grid[y1, x1] == 1:  # If the point is an obstacle, no visibility
                visible_points = set()
            else:
                for y2 in range(grid.shape[0]):
                    for x2 in range(grid.shape[1]):
                        p2 = (x2, y2)
                        line = bresenham(p1, p2)
                        rows, cols = zip(*line)
                        values = np.array(grid[np.array(rows), np.array(cols)])
                        indices = np.where(values == 1)[0]  # Get indices of 1
                        if len(indices) == 0:
                            visible_points = visible_points.union(set(line))
                        else:
                            visible_points = visible_points.union(set(line[0:indices[0]]))
        
        visibility_queue.put((task, list(visible_points)))

def worker_pool(matrix, num_agents, chunk_size):
    grid_size = matrix.shape[0]  # Assuming the matrix is square (10x10)
    all_points = [(x, y) for y in range(grid_size) for x in range(grid_size)]  # Generate all (x, y) points

    # Divide into chunks
    tasks = [all_points[i:i + chunk_size] for i in range(0, len(all_points), chunk_size)]  # Divide points into chunks

    print(f"Total tasks: {len(tasks)}")  # Remark the total number: easier for debug later

    # Visibility queues
    task_queue = multiprocessing.Queue()
    visibility_queue = multiprocessing.Queue()

    # Get from the task queue
    for task in tasks:
        task_queue.put(task)

    # Agent processes
    agents = []
    for agent_id in range(num_agents):
        p = multiprocessing.Process(target=agent, args=(task_queue, visibility_queue, agent_id, matrix))
        p.start()
        agents.append(p)

    # Stop agents
    for _ in range(num_agents):
        task_queue.put(None)

    # Collect results
    visibility_dict = {}
    for _ in range(len(tasks)):
        task, result = visibility_queue.get()
        for point in task:
            visibility_dict[str(point)] = result

    # Wait for all agents to finish
    for p in agents:
        p.join()

    # Save to JSON file
    with open("visibility_output1.json", "w") as file:
        json.dump(visibility_dict, file)

if __name__ == '__main__':
    # Example 10x10 matrix
    matrix = np.array([
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 1, 0, 0, 0],
        [0, 0, 1, 0, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 0, 0, 0, 0]
    ])

    # Testing worker_pool
    worker_pool(matrix, num_agents=2, chunk_size=2)