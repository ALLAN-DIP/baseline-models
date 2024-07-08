from sklearn.neighbors import KNeighborsClassifier
import os
import json
import numpy as np

def entry_to_vectors(phase):
    state = phase["state"]
    orders = phase["orders"]

    fields = ["powers", "centers", "homes", "influence"]
    regions = ['ADR', 'ALB', 'MAO', 'RUM', 'BLA', 'LVN', 'TYR', 'SPA', 'PIE', 'APU', 'FIN', 'IRI',
               'ANK', 'LVP', 'NTH', 'CLY', 'SEV', 'SMY', 'SYR', 'ION', 'MUN', 'UKR', 'TUN', 'SIL',
               'DEN', 'EDI', 'WAL', 'SKA', 'MOS', 'ROM', 'GAL', 'TUS', 'PIC', 'VEN', 'ENG', 'POR',
               'PAR', 'HEL', 'WES', 'PRU', 'LON', 'NWY', 'TRI', 'YOR', 'BUD', 'HOL', 'CON', 'BUR',
               'BER', 'EAS', 'SER', 'ARM', 'NWG', 'AEG', 'NAP', 'TYS', 'SWE', 'BEL', 'RUH', 'KIE',
               'NAO', 'BOH', 'LYO', 'GRE', 'GAS', 'STP', 'NAF', 'BAR', 'BAL', 'BRE', 'VIE', 'BUL', 'MAR', 'WAR', 'BOT']
    centers = ['MAR', 'ANK', 'SER', 'RUM', 'GRE', 'PAR', 'BUL', 'TUN', 'SWE', 'POR', 'EDI', 'VIE',
               'MUN', 'WAR', 'BUD', 'BRE', 'KIE', 'LVP', 'SEV', 'CON', 'SMY', 'BEL', 'NWY', 'HOL',
               'STP', 'SPA', 'NAP', 'BER', 'TRI', 'MOS', 'DEN', 'ROM', 'LON', 'VEN']
    homes = ['ANK', 'PAR', 'BRE', 'MAR', 'MUN', 'VIE', 'SMY', 'TRI', 'NAP', 'BER', 'EDI', 'LVP',
             'KIE', 'VEN', 'LON', 'CON', 'SEV', 'ROM', 'BUD', 'WAR', 'STP', 'MOS']
    powers = ['AUSTRIA', 'ENGLAND', 'FRANCE', 'GERMANY', 'ITALY', 'RUSSIA', 'TURKEY']

    classes = np.ndarray([len(powers)], dtype=object)

    """
    # Old attributes
    attributes = np.ndarray([len(fields)], dtype=object)
    for i, field in enumerate(fields):
        attributes[i] = state[field]
    """

    
    units_data = state["units"]
    centers_data = state["centers"]
    homes_data = state["homes"]
    influences_data = state["influence"]
    n_powers = len(powers)

    units_atr = np.zeros([n_powers * 2 * len(regions)], dtype=bool)
    centers_atr = np.zeros([n_powers * len(centers)], dtype=bool)
    homes_atr = np.zeros([n_powers * len(homes)], dtype=bool)
    influences_atr = np.zeros([n_powers * len(regions)], dtype=bool)

    for j, power in enumerate(powers):
        # Units
        if power in units_data:
            if not units_data[power] is None:
                for i, region in enumerate(regions):
                    if f"A {region}" in units_data[power]:
                        units_atr[2 * i * n_powers + j] = 1
                    elif f"F {region}" in units_data[power]:
                        units_atr[i * 2 * n_powers + j + 1] = 1
        # Centers
        if power in centers_data:
            if not centers_data[power] is None:
                for i, center in enumerate(centers):
                    if center in centers_data[power]:
                        centers_atr[i * n_powers + j] = power
        # Homes
        if power in homes_data:
            if not homes_data[power] is None:
                for i, home in enumerate(homes):
                    if home in homes_data[power]:
                        homes_atr[i * n_powers + j] = power
        # Influence
        if power in influences_data:
            if not influences_data[power] is None:
                for i, inf in enumerate(regions):
                    if inf in influences_data[power]:
                        influences_atr[i * n_powers + j] = power

    attributes = np.concatenate((units_atr, centers_atr, homes_atr, influences_atr))

    # Discretisation of orders as strings
    for i, power in enumerate(powers):
        if power in orders:
            if not orders[power] is None:
                classes[i] = sorted(orders[power])
            else:
                classes[i] = list()
        else:
            classes[i] = list()
        
    return attributes, str(classes)

def run_knn(train_path, test_path):
    x = list()
    y = list()
    k = 1

    with open(train_path, 'r') as train:
        for line in train:
            game = json.loads(line)
            for phase in game["phases"]:
                vectors = entry_to_vectors(phase)
                x.append(vectors[0])
                y.append(vectors[1])

    model = KNeighborsClassifier(n_neighbors=k, weights='uniform', algorithm='ball_tree', metric="hamming")
    model.fit(x, y)
    
    test_data = list()
    true_labels = list()
    with open(test_path, 'r') as test:
        for line in test:
            game = json.loads(line)
            for phase in game["phases"]:
                vectors = entry_to_vectors(phase)
                test_data.append(vectors[0])
                true_labels.append(vectors[1])
    
    pred_labels = model.predict(test_data)
    print(true_labels[0])


def main():
    data_path = os.path.join("D:", os.sep, "Downloads", "dipnet-data-diplomacy-v1-27k-msgs", "test")
    train_path = os.path.join(data_path, "train.jsonl")
    test_path = os.path.join(data_path, "test.jsonl")

    run_knn(train_path, test_path)


if __name__ == "__main__":
    main()