from pathlib import Path
import subprocess
import json
import random
import ast
import statistics
import time
import numpy as np
import os

root_dir = "rust_data"

times = {}

def rust_launcher(width, height, image_name, file_name,repeat,subsub,thread_count):
    global times
    time_total = 0
    for i in range(repeat):
        args = ["cargo", "run", "--release", "--"] + [f"{width}x{height}", image_name, file_name, str(thread_count)]
        start = time.time()
        result = subprocess.run(args)
        end = time.time()
        time_total += (end-start)

    average = time_total/repeat
    if subsub in times.keys():
        times[subsub].append(average)
    else:
        times[subsub] = [average]
    print(average)
    print()

def dictionary_import(file_path,world_name,width,height,subsub,thread_count):
    image = file_path + "/" +  world_name
    json_image = file_path + world_name[:-4] + ".json"
    file_path = Path(json_image)

    
    rust_launcher(width,height,image,json_image,10,subsub,thread_count)
    

thread_averages = []

for thread_count in [1,2,4,8,16]:
    times = {}

    for subfolder in os.listdir(root_dir):
        subfolder_path = os.path.join(root_dir, subfolder)

        if os.path.isdir(subfolder_path):
            # Loop through sub-subfolders
            for subsub in os.listdir(subfolder_path):
                subsub_path = os.path.join(subfolder_path, subsub)

                if os.path.isdir(subsub_path):
                    # Look for image files in sub-subfolder
                    for file in os.listdir(subsub_path):
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                            image_name = file
                            image_folder_path = subsub_path  # without image name

                            #print(f"Image Name     : {image_name}")
                            #print(f"Image Path     : {image_folder_path}")
                            #print(f"Top Subfolder  : {subfolder}")
                            #print("-" * 40)
                    
                            dictionary_import(image_folder_path,image_name,subfolder,subfolder,subsub,thread_count)
    values = []
    for key in times.keys():
        average = statistics.mean(times[key])
        values.append(average)
    thread_averages.append(list(values))

    np.save('my_matrix'+str(thread_count)+'.npy', np.matrix(values))


print()