import os
import json

def main():
    path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs")
    filepath = os.path.join(path, "standard_no_press.jsonl")
    
    with open(filepath, 'r') as file:
        for line in file:
            entry = json.loads(line)
            print(entry.keys())
            print(entry["map"])
            print(entry["rules"])
            for i, phase in enumerate(entry["phases"]):
                print(phase.keys())
                print(phase["state"])
                if i == 10:
                    break
            break
        

if __name__ == "__main__":
    main()