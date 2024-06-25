import os
import json

class Knn_Model:
    def __init__(self):
        self.data = list()
        
    def get_state_dist(self, state, other):
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
    
    def get_order_dist(self, orders, other):
        dist = 0

        """
        Using same naive Hamming distance metric as above
        """

        for nation in orders.keys():
            if orders[nation] == None:
                continue
            elif not nation in other.keys():
                dist += len(orders[nation])
            elif other[nation] == None:
                dist += len(orders[nation])
            else:
                for unit in orders[nation]:
                    dist += not unit in other[nation]
        for nation in other.keys():
            if other[nation] == None:
                continue
            elif not nation in orders.keys():
                dist += len(other[nation])
            elif orders[nation] == None:
                dist += len(other[nation])
            else:
                for unit in other[nation]:
                    dist += not unit in orders[nation]

        return dist



    def train(self, train_path):
        with open(train_path, 'r') as src:
            for line in src:
                game = json.loads(line)
                for phase in game["phases"]:
                    self.data.append((phase["state"], phase["orders"]))

    def eval(self, test_path):
        pairs = list()
        with open(test_path, 'r') as src:
            for line in src:
                game = json.loads(line)
                for phase in game["phases"]:
                    state = phase["state"]
                    order = phase["orders"]
                    true = (state, order)

                    choices = sorted(self.data, key=lambda x : self.get_state_dist(state, x[0]))
                    chosen = choices[0]

                    state_score = self.get_state_dist(state, chosen[0])
                    orders_score = self.get_order_dist(order, chosen[1])
                    pairs.append((true, chosen, state_score, orders_score))
                break
        return pairs

def main():
    data_path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "test")
    train_path = os.path.join(data_path, "train.jsonl")
    test_path = os.path.join(data_path, "test.jsonl")
    knn = Knn_Model()
    knn.train(train_path)

    pairs = knn.eval(test_path)
    for true, chosen, state_score, orders_score in pairs:
        print(f"True choice:\n{true[1]}\n\nChosen choice:\n{chosen[1]}\n\nState score: {state_score}\nOrders score: {orders_score}")

if __name__ == "__main__":
    main()