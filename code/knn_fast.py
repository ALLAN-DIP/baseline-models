from sklearn.neighbors import KNeighborsClassifier
import os
import json
import numpy as np
from constants import *
from preprocess import decode_class, entry_to_vectors
from time import time

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

def run_knn(train_path, test_path):
    x = list()
    y = list()
    k = 10

    print("Preprocessing training data")
    with open(train_path, 'r') as train:
        for line in train:
            game = json.loads(line)
            for phase in game["phases"]:
                vectors = entry_to_vectors(phase)
                x.append(vectors[0])
                y.append(vectors[1])

    print("Training model")
    model = KNeighborsClassifier(n_neighbors=k, weights='uniform', algorithm='ball_tree', metric="hamming")
    model.fit(x, y)
    
    print("Preprocessing testing data")
    test_data = list()
    true_labels = list()
    with open(test_path, 'r') as test:
        for line in test:
            game = json.loads(line)
            for phase in game["phases"]:
                vectors = entry_to_vectors(phase)
                test_data.append(vectors[0])
                true_labels.append(vectors[1])
    
    print("Evaluating model")
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
    data_path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "medium")
    train_path = os.path.join(data_path, "train.jsonl")
    test_path = os.path.join(data_path, "test.jsonl")

    run_knn(train_path, test_path)


if __name__ == "__main__":
    start_time = time()
    main()
    print(f"Total runtime: {(time() - start_time):.2f} seconds")