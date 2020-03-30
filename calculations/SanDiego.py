import calculations.Calculator as Calculator
import calculations.City as City
import database as db
import math

class CalculatorSanDiego(Calculator.Calculator):
    #all implementations in Calculator class designed to work by default for San Diego
    # def __init__(self, name):
    #     super().__init__(name)
    pass

address_table = "sandiego_addresses"
parcels_table = "sandiego_parcels"
zones_table = "sandiego_zones"
transit_priority_table = "sandiego_transit_priority"
zoneinfo_table = "sandiego_zoneinfo"
affordable_table = "sandiego_affordable"

class SanDiego(City.AddressQuery):
    city = "San Diego"
    san_diego_calc = CalculatorSanDiego(city, zoneinfo_table, affordable_table)

    def get(self, street_address=None, apn=None) ->dict:
        affordable_minimum = 5 #TODO: don't hardcode this

        select_list = ["a.apn", "a.addrnmbr", "a.addrname", "a.addrsfx", "a.community", "a.addrzip", "a.parcelid",
                       "p.own_name1", "p.own_name2", "p.own_name3", "p.own_addr1", "p.own_addr2", "p.own_addr3",
                       "p.own_addr4", "p.own_zip", "p.shape_star", "p.shape_stle", "p.geometry",
                       "p.legldesc", "p.asr_land", "p.asr_impr"]
        data_query = """
                     SELECT {0}
                     FROM sandiego_addresses a, sandiego_parcels p
                     WHERE a.parcelid = p.parcelid AND {1}
                     LIMIT 1;
                     """

        if street_address:
            cond = "LOWER(CONCAT_WS(' ', a.addrnmbr, a.addrname, a.addrsfx)) = '{0}'".format(street_address.strip())
        elif apn:
            apn = [c for c in apn if c.isdigit()]
            cond = "a.apn = '{0}'".format(apn)
        else:
            raise Exception("Must contain either street_address or apn")

        db.cur.execute(data_query.format(','.join(select_list), cond))
        result = db.cur.fetchone()
        data_feature = {}
        for col, val in zip(select_list, result):
            if '.' in col: key = col.split('.')[1]
            else: key = col
            data_feature[key] = val
        print(data_feature)

        feature_to_sql = {"street_number": "addrnmbr",
                          "street_name": "addrname",
                          "street_sfx": "addrsfx",
                          "city": "community",
                          "zip": "addrzip",
                          "parcel_id": "parcelid",
                          "apn": "apn"}
        for f, s in feature_to_sql.items():
            self.data[f] = data_feature[s]
            if isinstance(self.data[f], float): self.data[f] = int(self.data[f])
            if self.data[f]: self.data[f] = str(self.data[f]).title()

        self.data["street_name_full"] = " ".join([self.data["street_number"], self.data["street_name"],
                                                  self.data["street_sfx"]])
        self.data["state"] = "CA"
        self.data["city_zip"] = " ".join([self.data["city"].title() + ",", self.data["state"], self.data["zip"]])
        self.data["address"] = " ".join([self.data["street_name_full"], self.data["city_zip"]])

        self.data["owner_name"] = "\n".join(list(filter(None, [data_feature[o] for o in ["own_name1",
                                                                                          "own_name2",
                                                                                          "own_name3"]])))
        self.data["owner_address"] = "\n".join(list(filter(None, [data_feature[o] for o in ["own_addr1", "own_addr2",
                                                                                              "own_addr3", "own_addr4",
                                                                                              "own_zip"]])))
        self.data["geometry"] = data_feature["geometry"]
        print("Getting Zoning data")

        self.data["zone"] = City.get_overlaps_one(self.data["geometry"], zones_table, "zone_name")
        self.data["zone_info_dict"] = self.san_diego_calc.zone_reader.get_rule_dict_output(self.data["zone"])
        self.data["lot_area"] = data_feature["shape_star"]
        print("Calculating density")

        max_density = self.san_diego_calc.get_attr_by_rule(self.data["zone"], 'max density')
        self.data["max_density"] = max_density[0]
        if len(max_density) > 1 and max_density[1] not in [None, '']:
            self.data["max_density_unit"] = max_density[1]
        else:
            self.data["max_density_unit"] = "sf per DU"
        self.data["base_dwelling_units"] = math.ceil(self.san_diego_calc.get_max_dwelling_units(
            self.data["lot_area"], self.data["zone"]))
        self.data["transit_priority"] = len(City.get_overlaps_all(self.data["geometry"], transit_priority_table)) > 0

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
