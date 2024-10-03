from diplomacy.engine.game import Game


def clean_input(input_list):
    return list(map(lambda x: x.replace('\\', ''), input_list))


def dict_to_state(state_dict):
    game = Game()
    for power in game.powers.values():
        name = power.name
        if name in state_dict["units"].keys():
            power.units = clean_input(state_dict["units"][name])
        if name in state_dict["centers"].keys():
            power.centers = clean_input(state_dict["centers"][name])
        if name in state_dict["influence"].keys():
            power.influence = clean_input(state_dict["influence"][name])
        if name in state_dict["homes"].keys():
            power.homes = clean_input(state_dict["homes"][name])
    phase = state_dict["name"]

    return game, phase
