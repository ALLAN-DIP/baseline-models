from custom_renderer import CustomRenderer
from diplomacy import Game
import os

DIR_PATH = os.path.join(os.getcwd(), "visualisation_code")
OUT_PATH = os.path.join(DIR_PATH, "out.svg")
ALT_PATH = os.path.join(DIR_PATH, "out_alt.svg")

game = Game("test")
renderer = CustomRenderer(game)

alterations = list(list() for p in game.powers.values())
print("\n".join(p.name for p in game.powers.values()))
alterations[0] = ["A BER - SIL"]
renderer.custom_render(output_path=OUT_PATH, alterations=alterations)
