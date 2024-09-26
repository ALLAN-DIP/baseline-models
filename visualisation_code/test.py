from custom_renderer import CustomRenderer
from diplomacy import Game
import os

DATA_PATH = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "medium")
DIR_PATH = os.path.join(os.getcwd(), "visualisation_code")
OUT_PATH = os.path.join(DIR_PATH, "out.svg")
ALT_PATH = os.path.join(DIR_PATH, "out_alt.svg")

game = Game("test")
renderer = CustomRenderer(game)

# alterations = list(list() for p in game.powers.values())
print("\n".join(p.name for p in game.powers.values()))
alterations_1 = [
    [("A BER - SIL", 1)],           # Austria
    [("F EDI C A LVP - NOR", 1)],   # England
    [("F PAR H", 1)],               # France
    [],                             # Germany
    [],                             # Italy
    [("A STP S MOS", 1)],           # Russia
    [("A SMY S F ANK - ARM", 1)]    # Turkey
]
alterations_2 = [
    [],
    [("F LON - NTH", 1), ("F LON - ENG", 0.75), ("F LON - YOR", 0.5)],
    [],
    [],
    [],
    [],
    []
]
renderer.custom_render(output_path=OUT_PATH, alterations=alterations_1)
renderer.custom_render(output_path=ALT_PATH, alterations=alterations_2)
