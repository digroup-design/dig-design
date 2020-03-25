import calculations.Calculator as Calculator
import calculations.GISReader as GISReader
import calculations.City as City
import dig.models as models
import math

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

class SanDiego(City.AddressQuery):
    city = "San Diego"
    san_diego_gis = GISSanDiego(city)
    san_diego_calc = CalculatorSanDiego(city)

    def get(self, street_address=None, apn=None) ->dict:
        affordable_minimum = 5 #TODO: don't hardcode this
        if street_address:
            address_feature = self.san_diego_gis.get_address_feature(street_address)
            self.data["apn"] = address_feature.apn
        elif apn: #TODO
            raise Exception("APN search currently not supported")
        else:
            raise Exception("Must contain either street_address or apn")

        parcel_feature = self.san_diego_gis.get_parcel_feature(address_feature.parcel_id)

        self.data["address"] = self.san_diego_gis.get_address_proper(address_feature)
        self.data["street_number"] = address_feature.number
        self.data["street_name"] = address_feature.street_name
        self.data["street_sfx"] = address_feature.street_sfx
        self.data["city"] = address_feature.city
        self.data["state"] = "CA"
        self.data["zip"] = address_feature.zip
        self.data["street_name_full"] = " ".join([self.data["street_number"], self.data["street_name"],
                                                  self.data["street_sfx"]]).title()
        self.data["city_zip"] = " ".join([self.data["city"].title() + ",", self.data["state"], self.data["zip"]])
        self.data["parcel_id"] = address_feature.parcel_id

        self.data["owner_name"] = " ".join([o for o in [parcel_feature.owner1, parcel_feature.owner2,
                                                        parcel_feature.owner3] if o is not None])
        self.data["owner_address"] = " ".join([o for o in [parcel_feature.owner_address_1, parcel_feature.owner_address_2,
                                                           parcel_feature.owner_address_3, parcel_feature.owner_address_4,
                                                           parcel_feature.owner_zip] if o is not None])
        self.data["zone"] = self.san_diego_gis.get_zone(parcel_feature)
        self.data["zone_info_dict"] = self.san_diego_calc.zone_reader.get_rule_dict_output(self.data["zone"])
        print("Lot area: ", parcel_feature.lot_area)
        self.data["lot_area"] = float(parcel_feature.lot_area)

        max_density = self.san_diego_calc.get_attr_by_rule(self.data["zone"], 'max density')
        self.data["max_density"] = max_density[0]
        if len(max_density) > 1 and max_density[1] not in [None, '']:
            self.data["max_density_unit"] = max_density[1]
        else:
            self.data["max_density_unit"] = "sf per DU"
        self.data["base_dwelling_units"] = math.ceil(
            self.san_diego_calc.get_max_dwelling_units(self.data["lot_area"], self.data["zone"]))
        self.data["transit_priority"] = self.san_diego_gis.is_transit_area(parcel_feature)

        if self.data["base_dwelling_units"] >= affordable_minimum:
            self.data["affordable_dict"] = self.san_diego_calc.get_max_affordable_bonus_dict(
                 math.ceil(self.data["base_dwelling_units"]), self.data["transit_priority"])
            total_dus = []
            for v in self.data["affordable_dict"].values():
                total_dus.append(v['total_units'])
            self.data["max_dwelling_units"] = max(total_dus)
        else:
            self.data["max_dwelling_units"] = self.data["base_dwelling_units"]
        self.data["dwelling_area_dict"] = self.san_diego_calc.get_dwelling_area_dict(self.data["zone"], self.data["lot_area"])
        if self.data["dwelling_area_dict"]:  # assumes first entry is max dwelling area
            self.data["base_buildable_area"] = self.data["dwelling_area_dict"][list(self.data["dwelling_area_dict"].keys())[0]]['area']

        return self.data
