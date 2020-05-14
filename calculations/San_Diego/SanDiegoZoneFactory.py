from calculations.San_Diego.SanDiegoZoneR import SanDiegoZoneR as R
from calculations.San_Diego.SanDiegoZoneC import SanDiegoZoneC as C
from calculations.San_Diego.SanDiegoZoneI import SanDiegoZoneI as I
from calculations.San_Diego.SanDiegoZoneCUPD import SanDiegoZoneCUPD as CUPD
from calculations.San_Diego.SanDiegoZoneCCPD import SanDiegoZoneCCPD as CCPD
from calculations.San_Diego.SanDiegoZoneMX import SanDiegoZoneMX as MX
from calculations.San_Diego.SanDiegoZoneA import SanDiegoZoneA as A
from calculations.San_Diego.SanDiegoZoneO import SanDiegoZoneO as O

class SanDiegoZoneFactory:
    """
    Factory class for querying all the different zones in San Diego
    """
    def __init__(self):
        self.zone_query = None
        self.data = None

    def get(self, zone: str, area: float = None, geometry: dict = None, transit_priority:bool=False,
            stories: int = None, attached: bool = False, decimals: int = 2) -> dict:

        zone = zone.upper().replace("CUPD-", '')
        if "-" in zone:
            zone_cat = zone.split("-")[0]
        else:
            zone_cat = zone

        if zone_cat.startswith("R"):
            self.zone_query = R()
        elif zone_cat.startswith("CCPD"):
            self.zone_query = CCPD()
        elif zone_cat.startswith("CU") or zone_cat.startswith("CT"):
            self.zone_query = CUPD()
        elif zone_cat.startswith("C"):
            self.zone_query = C()
        elif zone_cat.startswith("I"):
            self.zone_query = I()
        elif zone_cat.startswith("O"):
            self.zone_query = O()
        elif zone_cat.startswith("A"):
            self.zone_query = A()
        elif zone_cat.endswith("MX"):
            self.zone_query = MX()
        else:
            raise ValueError("Zone name not valid")

        self.data = self.zone_query.get(zone, area, geometry, transit_priority, stories, attached, decimals)
        return self.data


