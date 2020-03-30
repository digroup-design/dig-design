import calculations.City as City
import simplejson as json
import database as db

address_table = "sanjose_addresses"
parcel_table = "sanjose_parcels"
zone_table = "sanjose_zones"

class SanJose(City.AddressQuery):
    def get(self, street_address=None, apn=None) ->dict:
        select_list = ["a.add_number", "a.feanme", "a.st_postypu", "a.inc_muni", "a.post_code", "a.fulladdres",
                       "a.fullmailin", "p.parcelid", "p.apn", "p.geometry"]
        data_query = """
                     SELECT {0}
                     FROM sanjose_addresses a, sanjose_parcels p
                     WHERE a.parcelid::TEXT = p.parcelid::TEXT AND {1}
                     LIMIT 1;
                     """

        if street_address:
            cond = "LOWER(a.fulladdres) = LOWER('{0}')".format(street_address.trim())
        elif apn:
            apn = ''.join([c for c in apn if c.isdigit()])
            cond = "p.parcelid = '{0}'".format(apn)
        else:
            raise Exception("Query needs either street_address or apn")

        db.cur.execute(data_query.format(",".join(select_list), cond))
        data_feature = {}
        for col, val in zip(select_list, db.cur.fetchone()):
            if '.' in col: key = col.split('.')[1]
            else: key = col
            data_feature[key] = val

        feature_to_sql = {"street_number": "add_number",
                          "street_name": "feanme",
                          "street_sfx": "st_postypu",
                          "city": "inc_muni",
                          "zip": "post_code",
                          "address": "fullmailin",
                          "street_name_full": "fulladdres",
                          "parcel_id": "parcelid",
                          "apn": "apn"}

        for f, s in feature_to_sql.items():
            self.data[f] = data_feature[s]
            if self.data[f]: self.data[f] = str(self.data[f])

        self.data["state"] = "CA"
        self.data["city_zip"] = "{0}, {1} {2}".format(self.data["city"], self.data["state"], self.data['zip'])
        self.data["geometry"] = json.loads(data_feature["geometry"].replace("'", '"'))

        self.data["zone"] = City.get_overlaps_many(self.data["geometry"], db.pg_find(zone_table, {}), "zoning")
        self.data["zone_info_dict"] = {} #TODO: Import data into db

        self.data["lot_area"] = 1000 #TODO
        self.data["lot_width"] = None #TODO
        self.data["dwelling_area_dict"] = {} #TODO: FAR calculations

        return self.data