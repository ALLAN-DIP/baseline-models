from sklearn.neighbors import KNeighborsClassifier
import os
import json
import numpy as np
from constants import *
from preprocess_v2 import generate_x_y
from preprocess_v2 import key_to_filename
from time import time
from evaluation_v2 import evaluate_model
import pickle

def run_knn(train_path, test_path, model_path):
    train_dict = dict()
    k_max = 10

    print("Preprocessing training data")
    with open(train_path, 'r') as train:
        generate_x_y(train_dict, train)

    #models = dict()
    keys = {}
    print("Training models")
    for unit, data in train_dict.items():
        print(f"Sample size for {unit}: {len(data[0])}")
        k = k_max
        if k_max > len(data[0]):
            k = len(data[0])

        #models[unit] = KNeighborsClassifier(n_neighbors=k, weights='uniform', algorithm='ball_tree', metric="hamming")
        #models[unit].fit(data[0], data[1])

        model = KNeighborsClassifier(n_neighbors=k, weights='uniform', algorithm='ball_tree', metric="hamming")
        model.fit(data[0], data[1])
    
        if model_path != None:
            with open(os.path.join(model_path, key_to_filename(unit)), 'wb') as model_file:
                pickle.dump(model, model_file)
    
    #if model_path != None:
    #    with open(model_path, 'wb') as model_file:
    #        pickle.dump(models, model_file)

    print("Preprocessing testing data")
    test_dict = dict()
    with open(test_path, 'r') as test:
        generate_x_y(test_dict, test)
    
    print("Evaluating model")
    results = evaluate_model(test_dict, model_path)
    print(results)

def main():
    data_path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "medium")
    train_path = os.path.join(data_path, "train.jsonl")
    test_path = os.path.join(data_path, "test.jsonl")
    model_path = os.path.join(data_path, "knn_models")

    run_knn(train_path, test_path, model_path)


if __name__ == "__main__":
    start_time = time()
    main()
    print(f"Total runtime: {(time() - start_time):.2f} seconds")