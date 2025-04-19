import json
import sys
import os

def load_and_sort_json(path):
    with open(path, 'r') as f:
        data = json.load(f)

    sorted_data = {}
    for key, value in data.items():
        # Sort each list of [x, y] pairs
        sorted_value = sorted(value, key=lambda coord: (coord[0], coord[1]))
        sorted_data[key] = sorted_value

    return sorted_data

def compare_sorted_jsons(file1, file2):
    data1 = load_and_sort_json(file1)
    data2 = load_and_sort_json(file2)

    keys1 = set(data1.keys())
    keys2 = set(data2.keys())

    only_in_1 = keys1 - keys2
    only_in_2 = keys2 - keys1
    common_keys = keys1 & keys2

    differing = {}

    for key in common_keys:
        if data1[key] != data2[key]:
            differing[key] = {
                "file1": data1[key],
                "file2": data2[key],

            }


    if differing:
        print(f"{file1} and {file2} have differing values for the following keys:")
        sample_key = next(iter(differing))
        print(f"\nKey: {sample_key}")
        print(f"{file1}: {differing[sample_key]['file1']}")
        print(f"{file2}: {differing[sample_key]['file2']}")

    return {
        "only_in_file1": only_in_1,
        "only_in_file2": only_in_2,
        "differing": differing
    }

if __name__ == "__main__":


    # Compare the json files from two folders

    folder1= "./dungeons_medium"
    folder2= "./C_implementation/json_output"
    #folder2= "./CPP_implementation/json_output"

    files1 = set(f for f in os.listdir(folder1) if f.endswith('.json'))
    files2 = set(f for f in os.listdir(folder2) if f.endswith('.json'))

    common_files = files1 & files2
    only_in_1 = files1 - files2
    only_in_2 = files2 - files1


    for fname in sorted(common_files):
        file1_path = os.path.join(folder1, fname)
        file2_path = os.path.join(folder2, fname)
        compare_sorted_jsons(file1_path, file2_path)



