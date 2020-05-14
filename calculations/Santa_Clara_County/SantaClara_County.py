from calculations.AddressQuery import AddressQuery, area

class SantaClara_County(AddressQuery):
    tables = {
        "addresses": "santaclara_county_addresses",
        "parcels": "santaclara_county_parcels",
        "zones": "santaclara_county_zones",
        "oz": "ca_opportunity_zones"
    }

    city_list = ('SAN JOSE', 'STANFORD', 'LOS ALTOS', 'LIVERMORE', 'PALO ALTO', 'ALVISO',
                 'CAMPBELL', 'SAN MARTIN', 'MOUNTAIN VIEW', 'SANTA CLARA', 'MORGAN HILL',
                 'REDWOOD ESTATES', 'GILROY', 'LOS GATOS', 'LOS ALTOS HILLS', 'PORTOLA VALLEY',
                 'SARATOGA', 'MILPITAS', 'SUNNYVALE', 'COYOTE', 'CUPERTINO', 'MONTE SERENO')

    def get(self, address=None, apn=None, city=None, state=None)->dict:
        """param city and state are not used for this class"""

        if address:
            cond = "a.full_addr = '{0}'".format(address.strip().upper())
        elif apn:
            cond = "p.apn = '{0}'".format(apn)
        else:
            raise TypeError("Query requires either address or apn")

        select_fields = ("a.city", "a.housenumte", "a.streetname", "a.streetpref", "a.streetsuff", "a.streettype",
                         "a.unitnumber", "a.zipcode", "p.apn", "p.shape_area", "p.shape_leng", "p.geometry",
                         "a.full_addr")
        tables = SantaClara_County.tables
        data_query = """
                     SELECT {0}
                     FROM {2} a, {3} p
                     WHERE a.apn = p.apn AND {1}
                     LIMIT 1;
                     """.format(",".join(select_fields), cond, tables["addresses"], tables["parcels"])
        self.cur.execute(data_query)
        result = self.cur.fetchone()
        if result:
            data_feature = {}
            for col, val in zip(select_fields, result):
                if '.' in col: key = col.split('.')[1]
                else: key = col
                data_feature[key] = val

            feature_to_sql = {"street_number": "housenumte",
                              "street_sfx": "streettype",
                              "city": "city",
                              "zip": "zipcode",
                              "apn": "apn",}

            for f, s in feature_to_sql.items():
                self.data[f] = data_feature[s]
                if self.data[f]: self.data[f] = str(self.data[f])

            self.data["street_name"] = " ".join(filter(None, [data_feature['streetpref'],
                                                              data_feature['streetname']]))
            self.data["street_name_full"] = data_feature["full_addr"].title()
            self.data["state"] = "CA"
            self.data["city_zip"] = " ".join(filter(None, [self.data["city"].title(), self.data["state"] + ",", self.data["zip"]]))
            self.data["address"] = ", ".join([self.data["street_name_full"], self.data["city_zip"]])
            self.data["geometry"] = data_feature["geometry"]

            geo_xy = self.st_transform(self.data["geometry"], out_proj=102643)
            self.data["lot_area"] = area(geo_xy)
            self.data["lot_width"] = data_feature["shape_leng"] / data_feature["shape_area"] * self.data["lot_area"]

            self.data["zone"] = self.find_intersects_one(self.data["geometry"], tables["zones"], "zoning")
            if self.data["zone"]:
                self.data["zone_info_dict"] = {} #TODO: Import data into db

                self.data["dwelling_area_dict"] = {} #TODO: FAR calculations
            self.data["assessor_map"] = "https://www.sccassessor.org/apps/ShowMapBook.aspx?apn={0}".format(
                self.data["apn"])
            self.data["opportunity_zone"] = self.find_intersects_one(self.data["geometry"], tables["oz"], "namelsad",
                                                                  parcel_proj=4326, zone_proj=4269)
        return self.data