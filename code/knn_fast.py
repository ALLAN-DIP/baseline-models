from sklearn.neighbors import KNeighborsClassifier
import os
import json
import numpy as np
from constants import *
from time import time

def encode_class(orders):
    classes = np.ndarray([len(POWERS)], dtype=object)
    for i, power in enumerate(POWERS):
        if power in orders:
            if not orders[power] is None:
                classes[i] = "^".join(sorted(orders[power]))
            else:
                classes[i] = ""
        else:
            classes[i] = ""


    encoding = "&".join(classes)
    return encoding

def decode_class(encoding):
    classes = np.array(encoding.split("&"))
    decoding = np.ndarray([len(POWERS)], dtype=object)
    for i, power in enumerate(POWERS):
        decoding[i] = classes[i].split("^")
    return decoding

def order_accuracy(predicted, true):
    # print(f"Predicted: {predicted}\nTrue: {true}\n")
    macro_correct = 0
    macro_total = len(POWERS)
    micro_correct = 0
    micro_total = 0

    for i, power in enumerate(POWERS):
        macro_correct += predicted[i] == true[i]
        for order in predicted[i]:
            micro_correct += order in true[i]
            micro_total += 1
        for order in true[i]:
            micro_correct += order in predicted[i]
            micro_total += 1
    return macro_correct, micro_correct, macro_total, micro_total

def entry_to_vectors(phase):
    state = phase["state"]
    orders = phase["orders"]

    FIELDS = ["powers", "centers", "homes", "influence"]


    """
    # Old attributes
    attributes = np.ndarray([len(fields)], dtype=object)
    for i, field in enumerate(fields):
        attributes[i] = state[field]
    """

    
    units_data = state["units"]
    centers_data = state["centers"]
    homes_data = state["homes"]
    influences_data = state["influence"]
    n_powers = len(POWERS)

    units_atr = np.zeros([n_powers * 2 * len(INFLUENCES)], dtype=bool)
    centers_atr = np.zeros([n_powers * len(CENTERS)], dtype=bool)
    homes_atr = np.zeros([n_powers * len(HOMES)], dtype=bool)
    influences_atr = np.zeros([n_powers * len(TERRITORIES)], dtype=bool)

    for j, power in enumerate(POWERS):
        # Units
        if power in units_data:
            if not units_data[power] is None:
                for i, region in enumerate(TERRITORIES):
                    if f"A {region}" in units_data[power]:
                        units_atr[2 * i * n_powers + j] = 1
                    elif f"F {region}" in units_data[power]:
                        units_atr[i * 2 * n_powers + j + 1] = 1
        # Centers
        if power in centers_data:
            if not centers_data[power] is None:
                for i, center in enumerate(CENTERS):
                    if center in centers_data[power]:
                        centers_atr[i * n_powers + j] = power
        # Homes
        if power in homes_data:
            if not homes_data[power] is None:
                for i, home in enumerate(HOMES):
                    if home in homes_data[power]:
                        homes_atr[i * n_powers + j] = power
        # Influence
        if power in influences_data:
            if not influences_data[power] is None:
                for i, inf in enumerate(TERRITORIES):
                    if inf in influences_data[power]:
                        influences_atr[i * n_powers + j] = power

    attributes = np.concatenate((units_atr, centers_atr, homes_atr, influences_atr))

    # Discretisation of orders as strings
    classes = encode_class(orders)
        
    return attributes, classes

def run_knn(train_path, test_path):
    x = list()
    y = list()
    k = 10

    with open(train_path, 'r') as train:
        for line in train:
            game = json.loads(line)
            for phase in game["phases"]:
                vectors = entry_to_vectors(phase)
                x.append(vectors[0])
                y.append(vectors[1])

    model = KNeighborsClassifier(n_neighbors=k, weights='uniform', algorithm='ball_tree', metric="hamming")
    model.fit(x, y)
    
    test_data = list()
    true_labels = list()
    with open(test_path, 'r') as test:
        for line in test:
            game = json.loads(line)
            for phase in game["phases"]:
                vectors = entry_to_vectors(phase)
                test_data.append(vectors[0])
                true_labels.append(vectors[1])
    
    pred_labels = model.predict(test_data)
    pred_orders = map(decode_class, pred_labels)
    true_orders = map(decode_class, true_labels)

    overall_macro_correct = 0
    overall_macro_total = 0
    overall_micro_correct = 0
    overall_micro_total = 0
    for pred, true in zip(pred_orders, true_orders):
        macro_correct, micro_correct, macro_total, micro_total = order_accuracy(pred, true)
        overall_macro_correct += macro_correct
        overall_macro_total += macro_total
        overall_micro_correct += micro_correct
        overall_micro_total += micro_total
    print(f"Macro Accuracy: {(100 * overall_macro_correct / overall_macro_total):.2f}%")
    print(f"Micro Accuracy: {(100 * overall_micro_correct / overall_micro_total):.2f}%")


def main():
    data_path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "large")
    train_path = os.path.join(data_path, "train.jsonl")
    test_path = os.path.join(data_path, "test.jsonl")

    run_knn(train_path, test_path)


if __name__ == "__main__":
    start_time = time()
    main()
    print(f"Total runtime: {(time() - start_time):.2f} seconds")