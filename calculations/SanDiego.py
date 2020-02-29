import calculations.Calculator as Calculator
import calculations.GISReader as GISReader
import dig.models as models

class CalculatorSanDiego(Calculator.Calculator):
    #all implementations in Calculator class designed to work by default for San Diego
    # def __init__(self, name):
    #     super().__init__(name)
    pass

class GISSanDiego(GISReader.GisDB):
    def _init_models(self):
        self.zone_model = models.SanDiego_Zone
        self.address_model = models.SanDiego_Address
        self.parcel_model = models.SanDiego_Parcel
        self.transit_model = models.SanDiego_TransitArea

    def is_transit_area(self, parcel_feature):
        transit_name = "Transit Priority Area"
        return self.is_in_zone(parcel_feature, transit_name, self.transit_model)

san_diego = CalculatorSanDiego("San Diego")

san_diego_gis = GISSanDiego("San Diego")