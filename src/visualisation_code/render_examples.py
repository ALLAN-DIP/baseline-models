from visualisation_code.custom_renderer import CustomRenderer
from visualisation_code.dict_to_state import dict_to_state
from visualisation_code.examples import EXAMPLE_RENDERS

import os
from argparse import ArgumentParser

DIR_PATH = os.path.join(os.getcwd(), "visualisation_code")
DATA_PATH = os.path.join(DIR_PATH, "examples.jsonl")
OUT_PATH = os.path.join(DIR_PATH, "output")


def render_maps(data_dict=EXAMPLE_RENDERS, output_path=OUT_PATH):
    for i, render_info in enumerate(data_dict):
        try:
            state = render_info["state"]
            alterations = render_info["alterations"]
        except KeyError:
            print(f"Entry of index {i} is missing the state or alterations item and will not be rendered")
            continue

        game, phase = dict_to_state(state)
        renderer = CustomRenderer(game, phase=phase)
        for j, alt in enumerate(alterations):
            renderer.custom_render(output_path=os.path.join(output_path, f"out_{i}.{j}.svg"), alterations=alt)
    print("Rendering complete")


def main():
    parser = ArgumentParser()
    parser.add_argument("-o", "--output_path", type=str, default=OUT_PATH)
    args = parser.parse_args()
    render_maps(output_path=args.output_path)


if __name__ == "__main__":
    main()
