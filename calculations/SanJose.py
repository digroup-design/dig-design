import calculations.AddressQuery as Q
import calculations.SantaClara_County as SantaClara_County

address_table = "sanjose_addresses"
parcel_table = "sanjose_parcels"
zone_table = "sanjose_zones"
EPSG_102643 = SantaClara_County.EPSG_102643

class SanJose(SantaClara_County.SantaClara_County):
    def get(self, address=None, apn=None, city=None, state=None)->dict:
        """param city and state are not used for this class"""

        if address:
            cond = "UPPER(a.fulladdres) = UPPER('{0}')".format(address.strip())
        elif apn:
            apn = Q.digits_only(apn)
            cond = "p.apn = '{0}'".format(apn)
        else:
            raise TypeError("Query requires either address or apn")

        select_list = ["a.add_number", "a.feanme", "a.st_postypu", "a.inc_muni", "a.post_code", "a.fulladdres",
                       "a.fullmailin", "p.parcelid", "p.apn", "p.geometry"]

        data_query = """
                     SELECT {0}
                     FROM sanjose_addresses a, sanjose_parcels p
                     WHERE a.parcelid::TEXT = p.parcelid AND {1}
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
            self.data["geometry"] = data_feature["geometry"]

            geo_xy = Q.transform_geometry(self.data["geometry"], out_proj=EPSG_102643)
            self.data["lot_area"] = Q.area(geo_xy)
            self.data["lot_width"] = None #TODO

            self.data["zone"] = self.get_overlaps_one(self.data["geometry"], zone_table, "zoning")
            if self.data["zone"]:
                self.data["zone_info_dict"] = {} #TODO: Import data into db

                self.data["dwelling_area_dict"] = {} #TODO: FAR calculations
            self.data["assessor_map"] = "https://www.sccassessor.org/apps/ShowMapBook.aspx?apn={0}".format(
                self.data["apn"])
        return self.data