from tqdm.auto import tqdm
import json
import numpy as np

from baseline_models.model_code.preprocess import get_season_phase, generate_key, generate_attribute, get_unit_from_order
from baseline_models.model_code.context_models.lr_context.params import MAX_CONTEXT, MIN_CONTEXT
from baseline_models.model_code.context_models.utils import sample_context
from baseline_models.model_code.context_models.order import Order, OrderType
from baseline_models.model_code.constants import CLASSNOORDER

class DataLoader:
    def __init__(self, 
                 fpath: str, 
                 n_games: int = None, 
                 is_test: bool = False,
                 n_encoding_from_powerset: int = 1
                 ):
        """
        Params:
            fpath (str): path to data json file
            n_games (int): number of games in the data
            is_test (bool): whether the dataset is for testing
                            (used for indication to sample test context)
            n_encoding_from_powerset (int): how many encodings to sample from powerset
        """
        self._data = dict()
        self._fpath = fpath
        self._n_games = n_games
        self._is_test = is_test
        self._n_encoding = n_encoding_from_powerset

    def extend_dataset(self, X: list, y: list, key: str):
        if not X or not y or not key:
            return
        if self._data.get(key) is None:
            self._data[key] = [[], []]
        self._data[key][0].extend(X)
        self._data[key][1].extend(y)

    def gen_contextual_encodings(target: str,
                                pow_orders: list,
                                state_encoding: np.ndarray,
                                n_encodings: int = 2
                                ):
        """
        Given target order and the orders of the same power,
        generate a list of encodings and its corresponding 
        list of targets where each encodes current state + contextual orders.

        Params:
            target (str): the target order 
            pow_orders (list): the list of orders filled by the same power
            state_encoding (np.ndarray): encoding of the state
            n_encodings (int): the number of encodings to generate for this target order
        
        Returns:
            X (list) - list of encodings
            y (list) - list of corresponding targets

        """
        X = []
        y = []

        sampled_contexts = []
        while len(sampled_contexts) < n_encodings:
            is_unique_sample = True
            sample = set(sample_context(target, pow_orders, min_n_context=MIN_CONTEXT, max_n_context=MAX_CONTEXT))
            for s in sampled_contexts:
                if sample == s:
                    is_unique_sample = False
                    break
            if is_unique_sample:
                sampled_contexts.append(sample)
            
        for context in sampled_contexts:
            context_encoding = [state_encoding]
            sample_size = len(context)
            noorder_count = MAX_CONTEXT - sample_size
            if noorder_count < 0:
                raise Exception("Error in sampling context")
            
            for order in context:
                context_encoding.append(Order(order=order).gen_encoding())
            
            for i in range(noorder_count):
                context_encoding.append(Order(order_type=OrderType.NOORDER).gen_encoding())

            X.append(np.concatenate(tuple(context_encoding)))
            y.append(target)

            return X, y
        
    def load_WA(self, 
                phase: dict, 
                season_phase: str, 
                state_encoding: np.ndarray):
        orders = phase.get("orders")
        state = phase.get("state")
        builds = state.get("builds")
        
        for power, build_info in builds.items():
            build_count = build_info.get("count")
            buildable_homes = build_info.get("homes")

            if build_count == 0: # no build
                continue

            pow_orders = orders.get(power)
            if pow_orders is None:
                pow_orders = []

            if self._is_test:
                pow_orders = Order.get_valid_orders(pow_orders, phase, check_void=False)
            else:
                pow_orders = Order.get_valid_orders(pow_orders, phase)

            if build_count > 0:
                if not buildable_homes:
                    continue

                noorder_homes = set(buildable_homes) # track homes that did not have new unit built

                for order in pow_orders:
                    order_type, order_info = Order.get_info(order)
                    if order_type != OrderType.BUILD_ARMY and order_type != OrderType.BUILD_FLEET:
                        continue

                    build_home = order_info.get("provinceDest").split("/")[0] # accounts for cases such as STP/NC
                    if build_home in noorder_homes:
                        noorder_homes.remove(build_home)
                    
                    X, y = DataLoader.gen_contextual_encodings(target=order, 
                                                               pow_orders=pow_orders, 
                                                               state_encoding=state_encoding,
                                                               n_encodings=self._n_encoding
                                                               )
                    key = generate_key(build_home, season_phase)
                    self.extend_dataset(X, y, key)

                for noorder in noorder_homes:
                    X, y = DataLoader.gen_contextual_encodings(target=CLASSNOORDER, 
                                                               pow_orders=pow_orders,
                                                               state_encoding=state_encoding,
                                                               n_encodings=self._n_encoding
                                                               )
                    key = generate_key(noorder, season_phase)
                    self.extend_dataset(X, y, key)
            
            else:
                units = state.get("units")
                if not units:
                    continue
                pow_units = units.get(power)
                if not pow_units:
                    continue

                noorder_units = set(pow_units) # track units that have no disband order
                for order in pow_orders:
                    order_type, order_info = Order.get_info(order)
                    unit = get_unit_from_order(order)
                    noorder_units.remove(unit)
                    X, y = DataLoader.gen_contextual_encodings(target=order,
                                                               pow_orders=pow_orders,
                                                               state_encoding=state_encoding,
                                                               n_encodings=self._n_encoding
                                                               )
                    key = generate_key(unit, season_phase)
                    self.extend_dataset(X, y, key)
                
                for noorder in noorder_units:
                    X, y = DataLoader.gen_contextual_encodings(target=CLASSNOORDER,
                                                               pow_orders=pow_orders,
                                                               state_encoding=state_encoding,
                                                               n_encodings=self._n_encoding
                                                               )
                    key = generate_key(noorder, season_phase)
                    self.extend_dataset(X, y, key)
        return
    

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
                    X, y = DataLoader.gen_contextual_encodings(target=order,
                                                               pow_orders=valid_pow_orders,
                                                               state_encoding=state_encoding,
                                                               n_encodings=self._n_encoding)
                    
                    self.extend_dataset(X=X, y=y, key=key)
    
    def load(self):
        self.dataset = dict()
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