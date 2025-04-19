import json
import os

def load_and_sort_json(path):
    with open(path, 'r') as f:
        data = json.load(f)

    # get the keys of the json file
    keys = list(data.keys())
    print(len(keys))


if __name__ == "__main__":


    # Compare the json files from two folders

    json_file= "./Java_implementation/json/visibility_output.json"
    load_and_sort_json(json_file)

