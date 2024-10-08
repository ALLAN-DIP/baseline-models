import os
import pickle
from time import time
import json
import numpy as np
from model_code.preprocess import key_to_filename
from model_code.preprocess import generate_attribute
from model_code.preprocess import get_season_phase
from model_code.preprocess import get_units

from visualisation_code.custom_renderer import render_from_prediction


RENDER_RESULT = True


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


def render_outputs(model_path, test_path, output_path, max_games=-1, max_phases=-1, max_units=-1):
    with open(test_path, 'r') as test:
        for i, line in enumerate(test):
            game = json.loads(line)
            for j, phase in enumerate(game["phases"]):
                state = phase["state"]
                name = state["name"]

                if name == "COMPLETED":
                    continue
                print(f"Current state: {name}")

                pred_probs = predict(model_path, state)
                sorted_probs = dict()

                # Taking the top three orders for each army
                for k, (unit, orders) in enumerate(pred_probs.items()):
                    sorted_probs[unit] = sorted(orders, key=lambda x: x[1], reverse=True)[:3]
                    if "/" in unit:
                        unit = unit[:-3]
                    file_name = f"output_{i}_{state["name"]}_{unit}.svg".replace(" ", "_")
                    print(file_name)
                    render_from_prediction(state, sorted_probs, os.path.join(output_path, file_name))
                    sorted_probs.clear()

                    if k == max_units - 1:
                        break

                if j == max_phases - 1:
                    break

            if i == max_games - 1:
                break


def main():
    data_path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "medium")
    test_path = os.path.join(data_path, "test.jsonl")
    model_path = os.path.join(data_path, "knn_models")
    output_path = os.path.join(os.getcwd(), "output")

    render_outputs(model_path, test_path, output_path, max_games=1, max_phases=1)


if __name__ == "__main__":
    start_time = time()
    main()
    print(f"Total runtime: {(time() - start_time):.2f} seconds")
