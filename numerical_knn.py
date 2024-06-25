import os
import json

class Knn_Model:
    def __init__(self):
        self.data = list()
        
    def get_dist(self, state, other):
        dist = 0
        
        """
        Units, Centers, Homes, Influence:
        Using naive Hamming distance metric
        Future ideas:
            - Use some measurement of geographic proximity
            - Score units at the same location with different types less harshly
            - Normalise contribution to distance for each field
            - Counteract length bias (longer non-matching fields are less correct than shorter non-matching fields)

        Civil Disorder, Builds:
        Ignoring for now
        """
        fields = ["units", "centers", "homes", "influence"]
        for field in fields:
            info = state[field]
            other_info = other[field]
            for nation in info.keys():
                if not nation in other_info.keys():
                    dist += len(info[nation])
                else:
                    for unit in info[nation]:
                        dist += not unit in other_info[nation]
            for nation in other_info.keys():
                if not nation in info.keys():
                    dist += len(other_info[nation])
                else:
                    for unit in other_info[nation]:
                        dist += not unit in info[nation]
        return dist

    def train(self, train_path):
        with open(train_path, 'r') as src:
            for line in src:
                game = json.loads(line)
                for phase in game["phases"]:
                    self.data.append((phase["state"], phase["orders"]))

    def infer(self, test_path):
        with open(test_path, 'r') as src:
            for line in src:
                game = json.loads(line)
                for phase in game["phases"]:
                    state = phase["state"]
                    choices = sorted(self.data, key=lambda x : self.get_dist(state, x[0]))
                    break
                chosen = choices[0]
                true = (state, phase["orders"])
                print(f"Chosen:\n{chosen}\n\nTrue:\n{true}")
                print(f"Distance: {self.get_dist(state, chosen[0])}")
                break
        return chosen

def main():
    data_path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "test")
    train_path = os.path.join(data_path, "train.jsonl")
    test_path = os.path.join(data_path, "test.jsonl")
    knn = Knn_Model()
    knn.train(train_path)
    knn.infer(test_path)

if __name__ == "__main__":
    main()