import os
import pickle
from time import time
import json
import numpy as np
from preprocess import key_to_filename
from preprocess import generate_attribute
from preprocess import get_season_phase
from preprocess import get_units

def predict(model_path, state):
        pred_orders = dict()
        attribute = generate_attribute(state)
        season_phase = get_season_phase(state)
        units = get_units(state)

        for unit in units:
            key = unit + " " + season_phase

            file_path = os.path.join(model_path, key_to_filename(key))
            if os.path.exists(file_path):
                with open(file_path, 'rb') as model_file:
                    model = pickle.load(model_file)
                    attribute = np.reshape(attribute, (1, -1))
                    pred_proba = model.predict_proba(attribute)

                    pred_order_proba = []
                    for order, prob in zip(model.classes_, pred_proba[0]):
                        pred_order_proba.append((order, prob))

                    pred_orders[unit] = pred_order_proba
            else:
                print(f"Model not found | key: {key}")
        return pred_orders


def main():
    data_path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "medium")
    test_path = os.path.join(data_path, "test.jsonl")
    model_path = os.path.join(data_path, "knn_models")

    with open(test_path, 'r') as test:
        for line in test:
            game = json.loads(line)
            for phase in game["phases"]:
                state = phase["state"]
                pred_proba = predict(model_path, state)
                print(pred_proba)
                break


if __name__ == "__main__":
    start_time = time()
    main()
    print(f"Total runtime: {(time() - start_time):.2f} seconds")