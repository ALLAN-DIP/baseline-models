import os
import pickle
from time import time
import json
import numpy as np
import argparse

from baseline_models.model_code.preprocess import key_to_filename
from baseline_models.model_code.preprocess import generate_attribute
from baseline_models.model_code.preprocess import get_season_phase
from baseline_models.model_code.preprocess import get_units

from baseline_models.visualisation_code.custom_renderer import render_from_prediction


RENDER_RESULT = True


def predict(model_path, state):
    pred_orders = dict()
    attribute = generate_attribute(state)
    season_phase = get_season_phase(state)
    units = get_units(state)

    for unit in units:
        if season_phase[-1] == 'R' and unit[0] != '*':
            continue

        unit = unit.replace("*", "")
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


def render_outputs(model_path, test_path, output_path, max_games=-1, max_phases=-1, max_units=-1, max_orders=100):
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

                # Taking the top number of orders for each army
                for k, (unit, orders) in enumerate(pred_probs.items()):
                    sorted_probs[unit] = sorted(orders, key=lambda x: x[1], reverse=True)[:min(max_orders, len(orders))]
                    if state["name"] == "F1906R":
                        print(sorted_probs)

                    # Scaling probabilities
                    scalar = sorted_probs[unit][0][1]
                    if scalar > 0:
                        for m in range(len(sorted_probs[unit])):
                            sorted_probs[unit][m] = (sorted_probs[unit][m][0], sorted_probs[unit][m][1] / scalar)

                    file_name = f"output_{i}_{state["name"]}_{unit.replace("/", "_")}.svg".replace(" ", "_")

                    render_from_prediction(state, sorted_probs, os.path.join(output_path, file_name))
                    sorted_probs.clear()

                    if k == max_units - 1:
                        break

                if j == max_phases - 1:
                    break

            if i == max_games - 1:
                break


def main():
    parent_dir = os.path.dirname(os.getcwd())

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-t", "--test_path", type=str, default=os.path.join(parent_dir, "data", "test.jsonl"))
    argparser.add_argument("-m", "--model_path", type=str, default=os.path.join(parent_dir, "models", "example"))
    argparser.add_argument("-o", "--output_path", type=str, default=os.path.join(parent_dir, "output"))
    argparser.add_argument("-g", "--max_games", type=int, default=-1)
    argparser.add_argument("-p", "--max_phases", type=int, default=-1)
    argparser.add_argument("-u", "--max_units", type=int, default=-1)
    argparser.add_argument("-s", "--max_suggestions", type=int, default=6)

    args = argparser.parse_args()
    test_path = args.test_path
    model_path = args.model_path
    output_path = args.output_path
    max_games = args.max_games
    max_phases = args.max_phases
    max_units = args.max_units
    max_orders = args.max_suggestions

    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    """
    Deprecated with argparse addition, but still useful as a reference

    data_path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "medium")
    test_path = os.path.join(data_path, "test.jsonl")
    model_path = os.path.join(data_path, "knn_models")
    model_path = os.path.join("D:", os.sep, "Downloads", "lr_24102024", "lr_24102024")
    output_path = os.path.join(os.getcwd(), "output")
    """

    render_outputs(
        model_path,
        test_path,
        output_path,
        max_games=max_games,
        max_phases=max_phases,
        max_units=max_units,
        max_orders=max_orders
    )


if __name__ == "__main__":
    start_time = time()
    main()
    print(f"Total runtime: {(time() - start_time):.2f} seconds")
