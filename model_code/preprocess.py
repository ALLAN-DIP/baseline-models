import numpy as np
from constants import *
import json
import re

def key_to_filename(key):
    return re.sub(r"[\\/ \s]", "_", key)

# entry_to_vectors returns 3 lists:
# [0] attributes: list of np array of attributes/features
# [1] classes: list of orders
# [2] keys: list of model types
def entry_to_vectors(phase):
    state = phase["state"]
    orders = phase["orders"]

    attributes = list()
    classes = list()
    keys = list()

    phase_data = state["name"]
    season_phase = phase_data[0] + phase_data[-1]

    attribute = generate_attribute(phase)

    for _, order_list in orders.items():
        if not order_list is None:
            for order in order_list:
                # parse unit from order
                order_terms = order.split(" ")
                unit = " ".join(order_terms[0:2])
                key = unit + " " + season_phase

                attributes.append(attribute)
                classes.append(order)
                keys.append(key)
        
    return attributes, classes, keys

def generate_attribute(phase):
    state = phase["state"]

    FIELDS = ["powers", "centers", "homes", "influence"]
    phases = {
        'SM' : 0,
        'FM' : 1,
        'WA' : 2,
        'SR' : 3,
        'FR' : 4,
        'CD' : 5
    }
    
    phase_data = state["name"] # get phase name e.g. W1901A
    units_data = state["units"] # dict of powers to their units e.g. "AUSTRIA": ["A SER","A TYR","F ADR"]
    centers_data = state["centers"] # dict of powers to centers under their control e.g. "AUSTRIA": ["BUD","TRI","VIE", "SER"]
    homes_data = state["homes"] # dict of starting territory of each power?
    influences_data = state["influence"] # dict of powers to the territories under their influence (territories that are last occupied by them)
    n_powers = len(POWERS)

    phase_atr = np.zeros([len(phases)], dtype=bool)
    units_atr = np.zeros([n_powers * 2 * len(INFLUENCES)], dtype=bool)
    centers_atr = np.zeros([n_powers * len(CENTERS)], dtype=bool)
    homes_atr = np.zeros([n_powers * len(HOMES)], dtype=bool)
    influences_atr = np.zeros([n_powers * len(TERRITORIES)], dtype=bool)

    season_phase = phase_data[0] + phase_data[-1] #get first and last letter of phase
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


    attribute = np.concatenate((phase_atr, units_atr, centers_atr, homes_atr, influences_atr))

    return attribute

def generate_x_y(groups, src):
    for line in src:
        game = json.loads(line)
        for phase in game["phases"]:
            vectors = entry_to_vectors(phase)

            for attribute, order, key in zip(vectors[0], vectors[1], vectors[2]):
                if not key in groups.keys():
                    groups[key] = (list(), list())
                groups[key][0].append(attribute)
                groups[key][1].append(order)
