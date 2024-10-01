from diplomacy.engine.game import Game


def dict_to_state(state_dict):
    game = Game()
    for power in game.powers.values():
        name = power.name
        if name in state_dict["units"].keys():
            power.units = state_dict["units"][name]
        if name in state_dict["centers"].keys():
            power.centers = state_dict["centers"][name]
        if name in state_dict["influence"].keys():
            power.influence = state_dict["influence"][name]
        if name in state_dict["homes"].keys():
            power.homes = state_dict["homes"][name]
    phase = state_dict["name"]

    return game, phase
