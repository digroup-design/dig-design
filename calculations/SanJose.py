import calculations.City as City
import calculations.GLOBALS as GLOBALS
import simplejson as json
import pymongo
import math

db = "san_jose"
address_collection = GLOBALS.client[db]["address"]
parcel_collection = GLOBALS.client[db]["parcels"]
zone_collection = GLOBALS.client[db]["zones"]

class SanJose(City.AddressQuery):

    def get(self, street_address=None, apn=None) ->dict:
        if street_address:
            field_list = []
            address_feature = City.concat_find(address_collection, street_address, field_list)
        elif apn:
            raise NotImplementedError("APN lookup feature not yet implemented")
        else:
            raise Exception("Query needs either street_address or apn")
        self.data["parcel_id"] = address_feature["parcel_id"]
        parcel_feature = parcel_collection.find({"parcel_id": self.data["parcel_id"]})
        return self.data