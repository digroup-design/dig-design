import calculations.City as City
import database as db

address_table = "santaclara_county_addresses"
parcel_table = "santaclara_county_parcels"
zone_table = "santaclara_county_zones"
EPSG_102643 = '+proj=lcc +lat_1=37.06666666666667 +lat_2=38.43333333333333\
 +lat_0=36.5 +lon_0=-120.5 +x_0=2000000 +y_0=500000.0000000002 +datum=NAD83 +units=us-ft +no_defs'

city_list = ['SAN JOSE', 'STANFORD', 'LOS ALTOS', 'LIVERMORE', 'PALO ALTO', 'ALVISO',
             'CAMPBELL', 'SAN MARTIN', 'MOUNTAIN VIEW', 'SANTA CLARA', 'MORGAN HILL',
             'REDWOOD ESTATES', 'GILROY', 'LOS GATOS', 'LOS ALTOS HILLS', 'PORTOLA VALLEY',
             'SARATOGA', 'MILPITAS', 'SUNNYVALE', 'COYOTE', 'CUPERTINO', 'MONTE SERENO']

class SantaClara_County(City.AddressQuery):
    def get(self, address=None, apn=None)->dict:
        if address:
            cond = "LOWER(CONCAT_WS(' ', a.housenumte, a.streetpref, a.streetname, a.streettype, a.streetsuff))\
             = LOWER('{0}')".format(address.strip())
        elif apn:
            apn = ''.join([c for c in apn if c.isdigit()])
            cond = "p.apn = '{0}'".format(apn)
        else:
            raise Exception("Query needs either street_address or apn")

        select_list = ["a.city", "a.housenumte", "a.streetname", "a.streetpref", "a.streetsuff", "a.streettype",
                       "a.unitnumber", "a.zipcode", "p.apn", "p.shape_area", "p.shape_leng", "p.geometry"]
        data_query = """
                     SELECT {0}
                     FROM santaclara_county_addresses a, santaclara_county_parcels p
                     WHERE a.apn = p.apn AND {1}
                     LIMIT 1;
                     """
        self.cur.execute(data_query.format(",".join(select_list), cond))
        result = self.cur.fetchone()
        if result:
            data_feature = {}
            for col, val in zip(select_list, result):
                if '.' in col: key = col.split('.')[1]
                else: key = col
                data_feature[key] = val

            feature_to_sql = {"street_number": "housenumte",
                              "street_sfx": "streettype",
                              "city": "city",
                              "zip": "zipcode",
                              "apn": "apn"}

            for f, s in feature_to_sql.items():
                self.data[f] = data_feature[s]
                if self.data[f]: self.data[f] = str(self.data[f])

            self.data["street_name"] = " ".join(filter(None, [data_feature['streetpref'],
                                                              data_feature['streetname']]))
            self.data["street_name_full"] = " ".join(filter(None, [data_feature['housenumte'],
                                                                   self.data["street_name"],
                                                                   data_feature['streettype'],
                                                                   data_feature['streetsuff'],])).title()
            self.data["state"] = "CA"
            self.data["city_zip"] = " ".join([self.data["city"].title(), self.data["state"] + ",", self.data["zip"]])
            self.data["address"] = ", ".join([self.data["street_name_full"], self.data["city_zip"]])
            self.data["geometry"] = data_feature["geometry"]

            geo_xy = City.transform_geometry(self.data["geometry"], out_proj=EPSG_102643)
            self.data["lot_area"] = City.shape(geo_xy).area
            self.data["lot_width"] = data_feature["shape_leng"] / data_feature["shape_area"] * self.data["lot_area"]

            self.data["zone"] = self.get_overlaps_one(self.data["geometry"], zone_table, "zoning")
            if self.data["zone"]:
                self.data["zone_info_dict"] = {} #TODO: Import data into db

                self.data["dwelling_area_dict"] = {} #TODO: FAR calculations
            self.data["assessor_map"] = "https://www.sccassessor.org/apps/ShowMapBook.aspx?apn={0}".format(
                self.data["apn"])
        return self.data