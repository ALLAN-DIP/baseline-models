from baseline_models.model_code.predict import predict_order
from baseline_models.model_code.preprocess import generate_attribute, get_units, get_retreats, get_season_phase

class PHASES:
    MOVEMENT="M"
    BUILD="WA"
    RETREAT="R"

class VisualAdvice:
    """
    Class for generating baseline model predictions to render visual move suggestions on game engine
    """
    def __init__(self, model_path: str, state: dict, power: str, province: str):
        """
        Class constructor

        Params:
            model_path (str) -- file path to model
            state (dict) -- dictionary storing current state information
            power (str) -- controlling power
            province (str) -- province selected
        """
        self.model_path = model_path
        self.state = state
        self.power = power
        self.province = province
        self.season_phase = None
        self.attribute = None
    
     # UTIL FUNCTIONS
    def set_season_phase(self):
        """
        Setter for season_phase using state dict
        """
        season_phase = get_season_phase(self.state["name"])
        if season_phase is not None:
            self.season_phase = season_phase
        return self.season_phase
    
    def set_attribute(self):
        """
        Setter for attribute using state dict
        """
        attr = generate_attribute(self.state)
        if attr is not None:
            self.attribute = attr
        return self.attribute
    
    def get_unit_from_province(units: list, province: str):
        """
        Retrieves a unit in the provided province 
        from a provided list of units

        Params:
            units (list) -- list of units 
            province (str) -- uppercase 3 letter code of the province
        """
        if units is None or province is None:
            return None
        for unit in units:
            if province == unit.split(" ")[1]:
                return unit
        return None

    def sort_preds(preds: dict, phase: PHASES, top_k: int):
        """
        Sort the predicted orders by their predicted probabilities in decreasing order

        Params:
            preds (dict) -- dictionary where each key is a unit, corresponding value is a 
            list of tuples of the form (possible_order, predicted_probabiltity)
            phase (PHASES) -- constant specifying whether phase is retreat, movement, or build
            top_k (int) -- integer specifying the orders returned are the top k highest probability orders 

        Returns:
            (dict) -- dictionary where each key is an order and its corresponding value is a dictionary
            storing its rank, predicted probability and rendering opacity. Rank is determined by predicted probability 
            sorted in decreasing order.
            e.g., {'A GAL R WAR': {'rank': 0, 'pred_prob': 0.3635689010282275, 'opacity': 1}, ...}
        """
        sorted_json = dict()
        sorted_orders = []
        
        for unit, orders in preds.items():
            sorted_orders = sorted(orders, key=lambda x: x[1], reverse=True)[:min(top_k, len(orders))]

        # convert to json for easier parsing to frontend
        for rank, (order, pred_prob) in enumerate(sorted_orders):
            sorted_json[order] = dict()
            sorted_json[order]["rank"] = rank
            sorted_json[order]["pred_prob"] = pred_prob
            sorted_json[order]["opacity"] = pred_prob/sorted_orders[0][1] # linearly scaled
        return sorted_json

    # PREDICT FUNCTIONS 
    def predict_build(self):
        """
        Predict build phase for power in selected province
        (PROVINCE DEPENDENT)
        
        Returns:
            (dict) -- dictionary where each key is a home/unit of the power
            and the corresponding value is a list of its possible orders and predicted probabilities.
        """
        preds = dict() # key=home, val=[(possible_order, pred_prob),...]

        # check invalid
        if self.state is None or self.power is None:
            return preds
        
        builds = self.state["builds"].get(self.power)
        if builds is None:
            return preds

        if builds["count"] == 0: # no builds
            return preds
        
        if builds["count"] > 0: # can add units
            homes = builds["homes"]
            if self.province in homes:
                preds = predict_order([self.province], self.season_phase, self.model_path, self.attribute)
            return preds

        else: # remove units
            units = get_units(self.state, self.power)
            disband_unit = VisualAdvice.get_unit_from_province(units, self.province)
            if disband_unit is not None:
                preds = predict_order([disband_unit], self.season_phase, self.model_path, self.attribute)
            return preds

    def predict_retreat(self):
        """
        Predict retreat phase for power in selected province
        (PROVINCE DEPENDENT)

        Returns:
            (dict) -- dictionary with one key being the retreating unit
            and the corresponding value is a list of its possible orders and predicted probabilities.
        """
        preds = dict()
        units = get_retreats(self.state, self.power)
        retreat_unit = VisualAdvice.get_unit_from_province(units, self.province)     
        
        if retreat_unit is None: # no retreat unit in province
            return preds
        
        if retreat_unit[0] == '*':
            retreat_unit = retreat_unit[1:]

        return predict_order([retreat_unit], self.season_phase, self.model_path, self.attribute)
    
    def predict_move(self):
        """
        Predict move phase for power in selected province
        (PROVINCE DEPENDENT)

        Returns:
            (dict) -- dictionary with one key being the moving unit
            and the corresponding value is a list of its possible orders and predicted probabilities.
        """
        preds = dict()
        units = get_units(self.state, self.power)
        move_unit = VisualAdvice.get_unit_from_province(units, self.province)
        if move_unit is None:
            return preds
        
        return predict_order([move_unit], self.season_phase, self.model_path, self.attribute)
    
    def predict(self, top_k: int = 5):
        """
        Predict orders for power in current phase. 

        Params:
            top_k (int) -- integer specifying the orders returned are the top k highest probability orders 

        Returns:
            (dict) -- dictionary storing top k orders predicted for power in current phase
            e.g., {'A GAL R WAR': {'rank': 0, 'pred_prob': 0.3635689010282275, "opacity": 1}, ...}
        """
        self.set_attribute()
        self.set_season_phase()
        phase = PHASES.MOVEMENT
        preds = dict()

        if self.model_path is None or self.model_path == "":
            return {"error": "Server unable to locate model"}

        if self.season_phase[-1] == PHASES.RETREAT:
            phase = PHASES.RETREAT
            preds = self.predict_retreat()
        
        elif self.season_phase == PHASES.BUILD:
            phase = PHASES.BUILD
            preds = self.predict_build()

        else:
            preds = self.predict_move()

        sorted_preds = VisualAdvice.sort_preds(preds, phase, top_k)

        return sorted_preds
