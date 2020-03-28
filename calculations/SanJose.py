import calculations.City as City
import calculations.GLOBALS as GLOBALS
import simplejson as json
import database as db

address_table = "sanjose_addresses"
parcel_table = "sanjose_parcels"
zone_table = "sanjose_zones"

class SanJose(City.AddressQuery):
    def get(self, street_address=None, apn=None) ->dict:
        if street_address:
            query_dict = {"fulladdres": street_address.trim()}
            address_feature = db.pg_find_one(address_table, query_dict, "i")
            self.data["parcel_id"] = str(address_feature["parcelid"])
            query_dict = {"parcelid": self.data["parcel_id"]}
            parcel_feature = db.pg_find_one(parcel_table, query_dict, "i")
            self.data["apn"] = str(parcel_feature["apn"])
        elif apn:
            self.data["apn"] = ''.join([c for c in apn if c.isdigit()])
            query_dict = {"apn": self.data["apn"]}
            parcel_feature = db.pg_find_one(parcel_table, query_dict, "i")
            self.data["parcel_id"] = parcel_feature["parcelid"]
            query_dict = {"parcelid": int(self.data["parcel_id"])}
            address_feature = db.pg_find(address_table, query_dict, "i")
        else:
            raise Exception("Query needs either street_address or apn")

        self.data["address"] = address_feature["fullmailin"]
        self.data["street_number"] = str(address_feature["add_number"])
        self.data["street_name"] = address_feature["feanme"]
        self.data["street_sfx"] = address_feature["st_postypu"]
        self.data["street_name_full"] = address_feature["fulladdres"]
        self.data["city"] = address_feature["inc_muni"]
        self.data["state"] = "CA"
        self.data["zip"] = address_feature["post_code"]
        self.data["city_zip"] = "{0}, {1} {2}".format(self.data["city"], self.data["state"], self.data['zip'])
        self.data["geometry"] = parcel_feature["geometry"]
        #getting zoning data
        zone_features = City.get_overlaps(self.data["geometry"], db.pg_find(zone_table, {}))
        self.data["zone"] = zone_features[0]["zoning"] #TODO: Find max coverage zones instead of assuming [0]
        self.data["zone_info_dict"] = {} #TODO: Import data into db

        self.data["lot_area"] = 1000 #TODO
        self.data["lot_width"] = None #TODO
        self.data["dwelling_area_dict"] = {} #TODO: FAR calculations

        return self.data

