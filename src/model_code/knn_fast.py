from sklearn.neighbors import KNeighborsClassifier
import os
from time import time
import pickle

from model_code.preprocess import generate_x_y
from model_code.preprocess import key_to_filename
from model_code.evaluation import evaluate_model


def run_knn(train_path, test_path, model_path):
    train_dict = dict()
    k_max = 10

    print("Preprocessing training data")
    with open(train_path, 'r') as train:
        generate_x_y(train_dict, train)

    print("Training models")
    for unit, data in train_dict.items():
        print(f"Sample size for {unit}: {len(data[0])}")
        k = k_max
        if k_max > len(data[0]):
            k = len(data[0])

        model = KNeighborsClassifier(n_neighbors=k, weights='uniform', algorithm='ball_tree', metric="hamming")
        model.fit(data[0], data[1])

        if model_path is not None:
            with open(os.path.join(model_path, key_to_filename(unit)), 'wb') as model_file:
                pickle.dump(model, model_file)

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
