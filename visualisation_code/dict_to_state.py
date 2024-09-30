from diplomacy.engine.game import Game

test = {"timestamp":1542990097232324,"zobrist_hash":"5744784867136166527","note":"","name":"F1907R","units":{"AUSTRIA":["A GAL"],"ENGLAND":["A HOL","A LVN","F BAL","F NTH","F KIE","A YOR","A STP","A WAR","A PRU","A SWE"],"FRANCE":["A RUH","A BEL","A BER","F MAO","F MAR","A BUD","A BOH","A MUN","F SPA/SC"],"GERMANY":[],"ITALY":["F GRE","F TUN","A TRI","A VEN","F ION","F AEG"],"RUSSIA":[],"TURKEY":["F BLA","A SEV","A ARM","A RUM","A SER","A MOS","A BUL","*A WAR"]},"centers":{"AUSTRIA":["BUD"],"ENGLAND":["EDI","LON","LVP","NWY","HOL","STP","DEN","MOS","SWE","KIE"],"FRANCE":["BRE","MAR","PAR","BEL","POR","SPA","MUN","BER","VIE"],"GERMANY":[],"ITALY":["NAP","ROM","VEN","TUN","TRI","GRE"],"RUSSIA":[],"TURKEY":["ANK","CON","SMY","BUL","RUM","SEV","SER","WAR"]},"homes":{"AUSTRIA":["BUD","TRI","VIE"],"ENGLAND":["EDI","LON","LVP"],"FRANCE":["BRE","MAR","PAR"],"GERMANY":["BER","KIE","MUN"],"ITALY":["NAP","ROM","VEN"],"RUSSIA":["MOS","SEV","STP","WAR"],"TURKEY":["ANK","CON","SMY"]},"influence":{"AUSTRIA":["ALB","GAL"],"ENGLAND":["LON","LVP","EDI","HOL","NAO","NWG","LVN","WAL","BAL","NTH","KIE","DEN","YOR","NWY","STP","WAR","PRU","SWE"],"FRANCE":["BRE","PAR","POR","MAR","GAS","LYO","RUH","BEL","PIC","BER","MAO","BUR","VIE","NAF","BUD","WES","BOH","MUN","SPA"],"GERMANY":[],"ITALY":["NAP","ROM","TYR","GRE","TYS","TUN","TRI","VEN","ION","AEG"],"RUSSIA":["FIN","SIL"],"TURKEY":["CON","SMY","BLA","ANK","SEV","UKR","ARM","RUM","SER","MOS","BUL"]},"civil_disorder":{"AUSTRIA":0,"ENGLAND":0,"FRANCE":0,"GERMANY":0,"ITALY":0,"RUSSIA":0,"TURKEY":0},"builds":{"AUSTRIA":{"count":0,"homes":[]},"ENGLAND":{"count":0,"homes":[]},"FRANCE":{"count":0,"homes":[]},"GERMANY":{"count":0,"homes":[]},"ITALY":{"count":0,"homes":[]},"RUSSIA":{"count":0,"homes":[]},"TURKEY":{"count":0,"homes":[]}},"game_id":"n4_TKUAjyrh_qqw-","map":"standard","rules":["NO_PRESS","POWER_CHOICE"],"retreats":{"AUSTRIA":{},"ENGLAND":{},"FRANCE":{},"GERMANY":{},"ITALY":{},"RUSSIA":{},"TURKEY":{"A WAR":["SIL","UKR"]}}} # noqa


def dict_to_state(state_dict):
    game = Game()
    for power in game.powers.values():
        print(power)
        name = power.name
        power.units = state_dict["units"][name]
        power.centers = state_dict["centers"][name]
        power.influence = state_dict["influence"][name]
        power.homes = state_dict["homes"][name]
        print(power)
    return game
