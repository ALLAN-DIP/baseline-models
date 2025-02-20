
from tqdm.auto import tqdm
import json
import numpy as np

from baseline_models.model_code.preprocess import get_season_phase, generate_key, generate_attribute, get_unit_from_order
from baseline_models.model_code.constants import CLASSNOORDER
from baseline_models.model_code.context_models.order import Order, OrderType
from baseline_models.model_code.context_models.utils import gen_test_context

class DataLoader:
    def __init__(self, 
                 fpath: str, 
                 n_games: int = None, 
                 is_test: bool = False):
        """
        Params:
            fpath (str): path to data json file
            n_games (int): number of games in the data
        """
        self._fpath = fpath
        self._data = dict()
        self._n_games = n_games
        self._is_test = is_test
    
    def append_data(self,
                    key: str,
                    state_encoding: np.ndarray,
                    y: str,
                    pow_orders: list):
        if self._data.get(key) is None:
            self._data[key] = [[], [], []]
        
        self._data[key][0].append(state_encoding)
        self._data[key][1].append(y)
        if self._is_test:
            test_context = gen_test_context(y, pow_orders)
            self._data[key][2].append(set(test_context))
        else:
            self._data[key][2].append(set(pow_orders))

    def load_WA(self,
                phase: dict, 
                season_phase: str, 
                state_encoding: np.ndarray
                ):
        orders = phase.get("orders")
        state = phase.get("state")
        if not state:
            return
        builds = state.get("builds")
        if not builds:
            return
        
        for power, build_info in builds.items():
            build_count = build_info.get("count")
            buildable_homes = build_info.get("homes")

            if build_count == 0: # no build
                continue

            pow_orders = orders.get(power)
            if pow_orders is None:
                pow_orders = []

            # orders filled by power
            if self._is_test:
                pow_orders = Order.get_valid_orders(pow_orders, phase, check_void=False)
            else:
                pow_orders = Order.get_valid_orders(pow_orders, phase)

            if build_count > 0: # buildable
                if not buildable_homes: # no buildable homes
                    continue

                noorder_homes = set(buildable_homes) # track homes that did not have new unit built
                for order in pow_orders:
                    order_type, order_info = Order.get_info(order)
                    if order_type != OrderType.BUILD_ARMY and order_type != OrderType.BUILD_FLEET:
                        continue

                    build_home = order_info.get("provinceDest").split("/")[0] # accounts for cases such as STP/NC
                    if build_home in noorder_homes:
                        noorder_homes.remove(build_home)

                    key = generate_key(build_home, season_phase)
                    self.append_data(key, state_encoding, order, pow_orders)
                
                for noorder in noorder_homes:
                    key = generate_key(noorder, season_phase)
                    self.append_data(key, state_encoding, CLASSNOORDER, pow_orders) 
            
            else: # disband
                units = state.get("units")
                if not units:
                    continue
                pow_units = units.get(power)
                if not pow_units:
                    continue

                noorder_units = set(pow_units)
                for order in pow_orders:
                    order_type, order_info = Order.get_info(order)
                    unit = get_unit_from_order(order)
                    noorder_units.remove(unit)
                    key = generate_key(unit, season_phase)
                    self.append_data(key, state_encoding, order, pow_orders)
                
                for noorder in noorder_units:
                    key = generate_key(noorder, season_phase)
                    self.append_data(key, state_encoding, CLASSNOORDER, pow_orders)
                
    def load_phase(self, 
                   phase: dict, 
                   season_phase: str, 
                   state_encoding: np.ndarray):
        if season_phase == "WA":
            self.load_WA(phase, season_phase, state_encoding)
        
        else:
            orders = phase.get("orders")
            if not orders:
                return
            for power, pow_orders in orders.items():
                if pow_orders is None:
                    continue

                if self._is_test:
                    valid_pow_orders = Order.get_valid_orders(pow_orders, phase, check_void=False)
                else:
                    valid_pow_orders = Order.get_valid_orders(pow_orders, phase)

                for order in valid_pow_orders:
                    unit = get_unit_from_order(order)
                    key = generate_key(unit, season_phase)
                    self.append_data(key, state_encoding, order, valid_pow_orders)

    def load(self):
        self._data = dict()
        data_type = "test" if self._is_test else "train"
        with open(self._fpath, "r") as src:
            for line in tqdm(src, total=self._n_games, desc=f"Loading {data_type} data"):
                game = json.loads(line)

                for phase in game["phases"]:
                    state = phase["state"]
                    season_phase = get_season_phase(state["name"])
                    state_encoding = generate_attribute(state)
                    self.load_phase(phase, season_phase, state_encoding)
        return self._data