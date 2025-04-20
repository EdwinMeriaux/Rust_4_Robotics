import multiprocessing
import json
import numpy as np
from typing import List, Any
from typing import Sequence, Tuple
import os
from pathlib import Path
import statistics
from PIL import Image
import time
from multiprocessing import Manager
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

def all_points_zero(grid: np.ndarray, points: Sequence[Tuple[int,int]]) -> bool:
    if not points:
        return True  
    rows, cols = zip(*points)
    return np.all(grid[rows, cols] == 0)

def agent(targets, visibility_queue, agent_id, grid,points):
    target_num = 0
    vision_dict = {}
    for target in targets:
        #if target_num % 100 == 0:
        #    print(target_num, "/", len(targets))
        for point in points:
            line = bresenham(point,target)
            
            clear = all_points_zero(grid,line)
            if clear == True:
                
                if str(target) in vision_dict.keys():
                    vision_dict[str(target)].append(point)
                else:
                    vision_dict[str(target)] = [point]
            else:
                if str(target) not in vision_dict.keys():
                    vision_dict[str(target)] = []
        target_num += 1

    
    visibility_queue.put(vision_dict)

def split_into_n(points: List[Any], n: int) -> List[List[Any]]:
    total = len(points)
    base_size, remainder = divmod(total, n)
    
    result = []
    start = 0
    for i in range(n):
        # Each of the first `remainder` groups gets an extra element
        size = base_size + (1 if i < remainder else 0)
        group = points[start:start + size]
        result.append(group)
        start += size
    return result

def worker_pool(image_name,subsub,image_folder_path,num_agents,number_runs):
    total_run_times = []
    print(image_folder_path + "/" + subsub + "/" + image_name + "_" + str(num_agents))
    for run in range(number_runs):

        start_time = time.time()
        img = Image.open(image_folder_path + "/" + subsub + "/" + image_name).convert('L')

        # Apply binary threshold: pixel > 128 becomes 255, else 0
        binary_img = img.point(lambda p: 255 if p > 128 else 0)

        # Convert to NumPy array
        matrix = np.array(binary_img)

        
        grid_size = matrix.shape[0]  # Assuming the matrix is square (10x10)
        all_points = [(x, y) for y in range(grid_size) for x in range(grid_size)]  # Generate all (x, y) points

        
        broken_tasks = split_into_n(all_points, num_agents)
        #print(f"Total tasks: {len(broken_tasks)}")  # Remark the total number: easier for debug later

        visibility_queue = manager.Queue()


        # Agent processes
        agents = []
        for agent_id in range(num_agents):
            p = multiprocessing.Process(target=agent, args=(broken_tasks[agent_id], visibility_queue, agent_id, matrix,all_points))
            p.start()
            agents.append(p)

        # Stop agents
        
        for p in agents:
            p.join()

        super_dict = {}

        while not visibility_queue.empty():
            super_dict = super_dict | visibility_queue.get()

        with open("visibility_output1.json", "w") as file:
            json.dump(super_dict, file)
        end_time = time.time()
        time_taken = end_time-start_time
        total_run_times.append(time_taken)
        print(time_taken)
    print()
    print(statistics.mean(total_run_times))
    print()
    full_data = [statistics.mean(total_run_times)] + total_run_times
    csv_path = image_folder_path + "/" + subsub + "/" + image_name#image_name
    csv_path = csv_path[:-4]
    csv_path += "_p_"
    csv_path += str(thread_count)
    csv_path += ".csv"
    np.savetxt(csv_path, full_data, delimiter=",")

root_dir = "rust_data"

times = {}

if __name__ == '__main__':
    thread_averages = []
    manager = multiprocessing.Manager()

    for thread_count in [4,]:#[16,8,4,2,1]
        times = {}

        for subfolder in ['50']:#os.listdir(root_dir): #['50', '100', '250']
            subfolder_path = os.path.join(root_dir, subfolder)

            if os.path.isdir(subfolder_path):
                # Loop through sub-subfolders
                for subsub in os.listdir(subfolder_path):
                    subsub_path = os.path.join(subfolder_path, subsub)

                    if os.path.isdir(subsub_path):
                        # Look for image files in sub-subfolder
                        for file in os.listdir(subsub_path):
                            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                                
                                worker_pool(file,subsub,subfolder_path,num_agents=thread_count,number_runs=5)
        values = []
        for key in times.keys():
            average = statistics.mean(times[key])
            values.append(average)
        thread_averages.append(list(values))

        np.save('my_matrix'+str(thread_count)+'.npy', np.matrix(values))


    # Testing worker_pool
    