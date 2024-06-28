import os
import json

def main():
    path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs")
    filepath = os.path.join(path, "other_maps.jsonl")
    messages_count = 0
    
    with open(filepath, 'r') as file:
        for line in file:
            entry = json.loads(line)
            # print(entry.keys())
            # print(entry["map"])
            # print(entry["rules"])
            for i, phase in enumerate(entry["phases"]):
                # print(phase.keys())
                # print(phase["orders"])
                # print(phase["orders"].keys())
                if len(phase["messages"]) > 0:
                    print(phase["messages"])
                    messages_count += 1
        print(messages_count)
        

if __name__ == "__main__":
    main()