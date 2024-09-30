from custom_renderer import CustomRenderer
from diplomacy import Game
from dict_to_state import dict_to_state, test

import os

DATA_PATH = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "medium")
DIR_PATH = os.path.join(os.getcwd(), "visualisation_code")
OUT_PATH = os.path.join(DIR_PATH, "output")


def test_alterations():
    game = Game("test")
    renderer = CustomRenderer(game)

    print("\n".join(p.name for p in game.powers.values()))
    alterations = [
        [
            [("A BER - SIL", 1)],           # Austria
            [("F EDI C A LVP - NOR", 1)],   # England
            [("F PAR H", 1)],               # France
            [],                             # Germany
            [],                             # Italy
            [("A STP S MOS", 1)],           # Russia
            [("A SMY S F ANK - ARM", 1)]    # Turkey
        ],
        [
            [],
            [("F LON - NTH", 1), ("F LON - ENG", 0.75), ("F LON - YOR", 0.5)],
            [],
            [],
            [],
            [],
            []
        ]
    ]

    for i, alt in enumerate(alterations):
        renderer.custom_render(output_path=os.path.join(OUT_PATH, f"out_{i}.svg"), alterations=alt)


def test_map_loading():
    game, phase = dict_to_state(test)
    renderer = CustomRenderer(game, phase=phase)

    alterations = [
        [
            [],
            [("F LON - NTH", 1), ("F LON - ENG", 0.75), ("F LON - YOR", 0.5)],
            [],
            [],
            [],
            [],
            []
        ]
    ]

    for alt in alterations:
        renderer.custom_render(output_path=os.path.join(OUT_PATH, "out.svg"), alterations=alt)


def main():
    test_alterations()
    test_map_loading()


if __name__ == "__main__":
    main()
