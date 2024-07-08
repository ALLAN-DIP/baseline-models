import os
import json

def main():
    path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs")
    filepath = os.path.join(path, "standard_no_press.jsonl")
    messages_count = 0
    
    with open(filepath, 'r') as file:
        codes = set()
        for i, line in enumerate(file):
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
                influences = phase["state"]["influence"]
                for infs in influences.values():
                    for inf in infs:
                        codes.add(inf)
            if i == 100:
                break
        print(codes, len(codes))


        print(messages_count)
        

if __name__ == "__main__":
    main()