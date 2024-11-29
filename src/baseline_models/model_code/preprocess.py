import numpy as np
from baseline_models.model_code.constants import *
import json
import re
from typing import TextIO


def key_to_filename(key: str) -> str:
    """
    Converts the unit's key to a filename friendly version

    Args:
        key (str): The key describing the unit's location
    Returns:
        (str): The filename version
    """
    return re.sub(r"[\\/ \s]", "_", key)


def entry_to_vectors(phase: dict) -> tuple:
    """
    Encodes a phase into a one hot encoding comprising of three lists:

    Args:
        phase (dict): The dictionary describing the current state
    Returns:
        (tuple): A tuple containing:
            [0] attributes: list of np array of attributes/features
            [1] classes: list of orders
            [2] keys: list of model types
    """
    state = phase["state"]
    orders = phase["orders"]

    attributes = list()
    classes = list()
    keys = list()

    season_phase = get_season_phase(state)
    attribute = generate_attribute(state)

    for _, order_list in orders.items():
        if order_list is not None:
            for order in order_list:
                order_terms = order.split(" ")
                unit = " ".join(order_terms[0:2])
                key = unit + " " + season_phase

                attributes.append(attribute)
                classes.append(order)
                keys.append(key)

    return attributes, classes, keys


def generate_attribute(state: dict) -> np.ndarray:
    """
    Encodes the power, centers, homes and influence components of the states into a one-hot vector

    Args:
        state (dict): The current game state
    Returns:
        (np.ndarray): The one-hot vector encoding
    """

    # FIELDS = ["powers", "centers", "homes", "influence"]
    phases = {
        'SM': 0,
        'FM': 1,
        'WA': 2,
        'SR': 3,
        'FR': 4,
        'CD': 5
    }

    units_data = state["units"]             # dict of powers to their units e.g. "AUSTRIA": ["A SER", "A TYR", "F ADR"]
    centers_data = state["centers"]         # dict of powers to centers under their control e.g. "AUSTRIA": ["BUD", "TRI", "VIE", "SER"]
    homes_data = state["homes"]             # dict of starting territory of each power?
    influences_data = state["influence"]    # dict of powers to the territories under their influence (territories that are last occupied by them)
    n_powers = len(POWERS)

    # Setting encoding sizes for each field
    phase_atr = np.zeros([len(phases)], dtype=bool)
    units_atr = np.zeros([n_powers * 2 * len(INFLUENCES)], dtype=bool)
    centers_atr = np.zeros([n_powers * len(CENTERS)], dtype=bool)
    homes_atr = np.zeros([n_powers * len(HOMES)], dtype=bool)
    influences_atr = np.zeros([n_powers * len(TERRITORIES)], dtype=bool)

    season_phase = get_season_phase(state)
    phase_atr[phases[season_phase]] = True

    for j, power in enumerate(POWERS):
        # Encoding units
        if power in units_data:
            if not units_data[power] is None:
                for i, region in enumerate(TERRITORIES):
                    if f"A {region}" in units_data[power] or f"*A {region}" in units_data[power]:
                        units_atr[2 * i * n_powers + j] = 1
                    elif f"F {region}" in units_data[power] or f"*F {region}" in units_data[power]:
                        units_atr[i * 2 * n_powers + j + 1] = 1
        # Encoding centers
        if power in centers_data:
            if not centers_data[power] is None:
                for i, center in enumerate(CENTERS):
                    if center in centers_data[power]:
                        centers_atr[i * n_powers + j] = power
        # Encoding homes
        if power in homes_data:
            if not homes_data[power] is None:
                for i, home in enumerate(HOMES):
                    if home in homes_data[power]:
                        homes_atr[i * n_powers + j] = power
        # Encoding influences
        if power in influences_data:
            if not influences_data[power] is None:
                for i, inf in enumerate(TERRITORIES):
                    if inf in influences_data[power]:
                        influences_atr[i * n_powers + j] = power

    # Combining encodings into one vector
    attribute = np.concatenate((phase_atr, units_atr, centers_atr, homes_atr, influences_atr))

    return attribute


def get_season_phase(state: dict) -> str:
    """
    Gets the current season phase type (for example "FM" is fall movement)
    """
    phase_data = state["name"]
    return phase_data[0] + phase_data[-1]


def get_units(state: dict) -> list:
    """
    Gets the list of active units from the current state
    """
    units = []
    units_data = state["units"]
    for _, unit_list in units_data.items():
        if unit_list is not None:
            for unit in unit_list:
                units.append(unit)
    return units


def generate_x_y(groups: dict, src: TextIO) -> None:
    """
    Generates (state, order) pairs from a file input stream
    """
    for line in src:
        game = json.loads(line)
        for phase in game["phases"]:
            vectors = entry_to_vectors(phase)

            for attribute, order, key in zip(vectors[0], vectors[1], vectors[2]):
                if key not in groups.keys():
                    groups[key] = (list(), list())
                groups[key][0].append(attribute)
                groups[key][1].append(order)
