import numpy as np
from constants import *

def encode_class(orders):
    classes = np.ndarray([len(POWERS)], dtype=object)
    for i, power in enumerate(POWERS):
        if power in orders:
            if not orders[power] is None:
                classes[i] = "^".join(sorted(orders[power]))
            else:
                classes[i] = ""
        else:
            classes[i] = ""


    encoding = "&".join(classes)
    return encoding

def decode_class(encoding):
    classes = np.array(encoding.split("&"))
    decoding = np.ndarray([len(POWERS)], dtype=object)
    for i, power in enumerate(POWERS):
        decoding[i] = classes[i].split("^")
    return decoding

def entry_to_vectors(phase):
    state = phase["state"]
    orders = phase["orders"]

    FIELDS = ["powers", "centers", "homes", "influence"]
    phases = {
        'SM' : 0,
        'FM' : 1,
        'WA' : 2,
        'SR' : 3,
        'FR' : 4,
        'CD' : 5
    }

    """
    # Old attributes
    attributes = np.ndarray([len(fields)], dtype=object)
    for i, field in enumerate(fields):
        attributes[i] = state[field]
    """

    phase_data = state["name"]
    units_data = state["units"]
    centers_data = state["centers"]
    homes_data = state["homes"]
    influences_data = state["influence"]
    n_powers = len(POWERS)

    phase_atr = np.zeros([len(phases)], dtype=bool)
    units_atr = np.zeros([n_powers * 2 * len(INFLUENCES)], dtype=bool)
    centers_atr = np.zeros([n_powers * len(CENTERS)], dtype=bool)
    homes_atr = np.zeros([n_powers * len(HOMES)], dtype=bool)
    influences_atr = np.zeros([n_powers * len(TERRITORIES)], dtype=bool)

    season_phase = phase_data[0] + phase_data[-1]
    phase_atr[phases[season_phase]] = True

    for j, power in enumerate(POWERS):
        # Units
        if power in units_data:
            if not units_data[power] is None:
                for i, region in enumerate(TERRITORIES):
                    if f"A {region}" in units_data[power] or f"*A {region}" in units_data[power]:
                        units_atr[2 * i * n_powers + j] = 1
                    elif f"F {region}" in units_data[power] or f"*F {region}" in units_data[power]:
                        units_atr[i * 2 * n_powers + j + 1] = 1
        # Centers
        if power in centers_data:
            if not centers_data[power] is None:
                for i, center in enumerate(CENTERS):
                    if center in centers_data[power]:
                        centers_atr[i * n_powers + j] = power
        # Homes
        if power in homes_data:
            if not homes_data[power] is None:
                for i, home in enumerate(HOMES):
                    if home in homes_data[power]:
                        homes_atr[i * n_powers + j] = power
        # Influence
        if power in influences_data:
            if not influences_data[power] is None:
                for i, inf in enumerate(TERRITORIES):
                    if inf in influences_data[power]:
                        influences_atr[i * n_powers + j] = power

    attributes = np.concatenate((phase_atr, units_atr, centers_atr, homes_atr, influences_atr))

    # Discretisation of orders as strings
    classes = encode_class(orders)
        
    return attributes, classes, season_phase