import re
import numpy as np

from baseline_models.model_code.constants import INFLUENCES
from baseline_models.model_code.context_models.constants import OrderFormat, OrderType, UnitType
from baseline_models.model_code.context_models.utils import gen_one_hot
from baseline_models.model_code.preprocess import get_unit_from_order

class Order:
    def __init__(self, order=None, order_type=None):
        self._str = order
        self._type = order_type
        self.encoding = None
    

    def get_info(order_str):
        """
        Given order string, returns its order type and extracted order attributes

        Return:
            (OrderType): order type
            (dict): dictionary storing order attributes
        """
        for form in OrderFormat:
            match = re.match(form.value, order_str)
            if not match:
                continue
            order_attrs = match.groupdict()
            # check provinces in order is valid
            for p in ["provinceA", "provinceB", "provinceDest"]:
                if order_attrs.get(p) is None:
                    continue
                if order_attrs[p] not in INFLUENCES:
                    raise Exception(f"Order {order_str} contains an invalid province '{order_attrs[p]}'")
            return OrderType[form.name], order_attrs
        raise Exception(f'Unrecognised order format {order_str}')
    
    def gen_encoding(self):
        """
        encoding format:
        OrderType(10), unitAType(2), unitAProvince(81), unitBType(2), unitBProvince(81), destProvince(81)
        """
        infoDict = {}
        if self._type != OrderType.NOORDER:
            self._type, infoDict = Order.get_info(self._str)
        
        # print(f'OrderType: {self._type.value}')
        _orderType = gen_one_hot(len(OrderType), self._type.value)
        
        
        # print(f'_unitAType: {infoDict.get("unitAType")}')
        _unitAType = gen_one_hot(len(UnitType), 
                                       UnitType[infoDict.get("unitAType")].value if infoDict.get("unitAType") is not None else None)
        
        # print(f'_unitAProvince: {infoDict.get("provinceA")}')
        _unitAProvince = gen_one_hot(len(INFLUENCES), 
                                           INFLUENCES.index(infoDict.get("provinceA")) if infoDict.get("provinceA") is not None else None)
        
        # print(f'_unitBType: {infoDict.get("unitBType")}')
        _unitBType = gen_one_hot(len(UnitType), 
                                       UnitType[infoDict.get("unitBType")].value if infoDict.get("unitBType") is not None else None)
        
        # print(f'_unitBProvince: {infoDict.get("provinceB")}')
        _unitBProvince = gen_one_hot(len(INFLUENCES), 
                                           INFLUENCES.index(infoDict.get("provinceB")) if infoDict.get("provinceB") is not None else None)
        
        # print(f'_destProvince: {infoDict.get("provinceDest")}')
        _destProvince = gen_one_hot(len(INFLUENCES), 
                                          INFLUENCES.index(infoDict.get("provinceDest")) if infoDict.get("provinceDest") is not None else None)
        
        self.encoding = np.concatenate((_orderType, _unitAType, _unitAProvince, _unitBType, _unitBProvince, _destProvince))
        return self.encoding
    
    def is_valid_order(order: str, phase: dict):
        """
        Check if order is valid (i.e., not illegal) in current phase
        
        Return:
            (bool): True if valid order else False
        """
        try:
            Order.get_info(order)
        except Exception as e:
            print(e)
            return False
        if phase.get("results") is None:
            return True
        unit = get_unit_from_order(order)
        return ((unit not in phase["results"]) or ("void" not in phase["results"][unit]))

    def get_valid_orders(orders_ls: list, phase: dict):
        """
        Filter a list of order strings to only include valid orders filled in current phase

        Return:
            (list): a list of valid order strings
        """
        return [order for order in orders_ls if Order.is_valid_order(order, phase)]