from enum import Enum

MIN_CONTEXT = 0
MAX_CONTEXT = 5

class UnitType(Enum):
    A = 0
    F = 1

class OrderType(Enum):
    HOLD=0
    MOVE=1
    MOVE_VIA=2
    CONVOY=3
    SUPPORT=4
    RETREAT=5
    DISBAND=6
    BUILD_ARMY=7
    BUILD_FLEET=8
    NOORDER=9

class OrderFormat(Enum):
    HOLD="^(?P<unitAType>[AF]) (?P<provinceA>[\w/]+) H$"
    MOVE="^(?P<unitAType>[AF]) (?P<provinceA>[\w/]+) - (?P<provinceDest>[\w/]+)$"
    MOVE_VIA="^(?P<unitAType>[AF]) (?P<provinceA>[\w/]+) - (?P<provinceDest>[\w/]+) VIA$"
    CONVOY="^(?P<unitAType>[AF]) (?P<provinceA>[\w/]+) C (?P<unitBType>[AF]) (?P<provinceB>[\w/]+) - (?P<provinceDest>[\w/]+)$"
    SUPPORT="^(?P<unitAType>[AF]) (?P<provinceA>[\w/]+) S (?P<unitBType>[AF]) (?P<provinceB>[\w/]+)( - (?P<provinceDest>[\w/]+)){0,1}$"
    RETREAT="^(?P<unitAType>[AF]) (?P<provinceA>[\w/]+) R (?P<provinceDest>[\w/]+)$"
    DISBAND="^(?P<unitAType>[AF]) (?P<provinceA>[\w/]+) D$"
    BUILD_ARMY="^A (?P<provinceDest>[\w/]+) B$"
    BUILD_FLEET="^F (?P<provinceDest>[\w/]+) B$"