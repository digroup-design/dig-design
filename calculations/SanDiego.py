from calculations.AddressQuery import AddressQuery
from calculations.SanDiegoZoneQuery import SanDiegoZoneQuery

class SanDiego(AddressQuery):
    tables = {
        "addresses": "sandiego_addresses",
        "parcels": "sandiego_parcels",
        "zones": "sandiego_zones",
        "transit_priority": "sandiego_transit_priority",
        "zone_info": "sandiego_zoneinfo",
        "affordable": "sandiego_affordable",
        "oz": "ca_opportunity_zones"
    }

    city_list = ('bonita', 'fallbrook', 'warner springs', 'ocotillo', 'ramona', 'pine valley', 'san marcos',
                 'el cajon', 'la jolla', 'borrego springs', 'campo', 'pala', 'palomar mountain', 'camp pendleton',
                 'aguanga', 'cardiff', 'dulzura', 'del mar', 'san diego', 'jacumba', 'olivenhain', 'potrero',
                 'imperial beach', 'julian', 'leucadia', 'rainbow', 'san clemente', 'santee', 'coronado', 'guatay',
                 'jamul', 'tecate', 'boulevard', 'spring valley', 'carlsbad', 'national city', 'imperial bch',
                 'encinitas', 'rancho santa fe', 'cardiff by the sea', 'oceanside', 'bonsall', 'descanso',
                 'rancho sante fe', 'lakeside', 'mount laguna', 'valley center', 'santa ysabel', 'alpine',
                 'lemon grove', 'pauma valley', 'ranchita', 'solana beach', 'la mesa', 'chula vista', 'san ysidro',
                 'escondido', 'poway')

    def get(self, address=None, apn=None, city=None, state=None) ->dict:
        """param city and state are not used for this class"""
        if address:
            cond = "a.full_addr = UPPER('{0}')".format(address.strip())
        elif apn:
            cond = "a.apn = '{0}'".format(apn)
        else:
            raise TypeError("Query requires either address or apn")

        select_fields = ("a.apn", "a.addrnmbr", "a.addrname", "a.addrsfx", "a.community", "a.addrzip", "a.parcelid",
                       "p.own_name1", "p.own_name2", "p.own_name3", "p.own_addr1", "p.own_addr2", "p.own_addr3",
                       "p.own_addr4", "p.own_zip", "p.shape_star", "p.shape_stle", "p.geometry",
                       "p.legldesc", "p.asr_land", "p.asr_impr", "a.full_addr")
        tables = SanDiego.tables
        data_query = """
                     SELECT {0}
                     FROM {2} a, {3} p
                     WHERE a.parcelid = p.parcelid AND {1}
                     LIMIT 1;
                     """.format(','.join(select_fields), cond, tables["addresses"], tables["parcels"])

        self.cur.execute(data_query)
        result = self.cur.fetchone()
        if result:
            data_feature = {}
            for col, val in zip(select_fields, result):
                if '.' in col: key = col.split('.')[1]
                else: key = col
                data_feature[key] = val

            feature_to_sql = {
                "street_number": "addrnmbr",
                "street_name": "addrname",
                "street_sfx": "addrsfx",
                "city": "community",
                "zip": "addrzip",
                "parcel_id": "parcelid",
                "apn": "apn",
                "street_name_full": "full_addr"
            }
            owner_name_fields = ("own_name1", "own_name2", "own_name3")
            owner_addr_fields = ("own_addr1", "own_addr2", "own_addr3", "own_addr4", "own_zip")

            for f, s in feature_to_sql.items():
                self.data[f] = data_feature[s]
                if isinstance(self.data[f], float): self.data[f] = int(self.data[f])
                if self.data[f]: self.data[f] = str(self.data[f]).title()

            self.data["state"] = "CA"
            self.data["owner_name"] = "\n".join(list(filter(None, [data_feature[o] for o in owner_name_fields])))
            self.data["owner_address"] = "\n".join(list(filter(None, [data_feature[o] for o in owner_addr_fields])))
            self.data["geometry"] = data_feature["geometry"]
            self.data["lot_area"] = data_feature["shape_star"]

            self.data["transit_priority"] = len(self.find_intersects_all(self.data["geometry"],
                                                                         tables["transit_priority"],
                                                                         "name")) > 0
            self.data["zone"] = self.find_intersects_one(self.data["geometry"], tables["zones"], "zone_name")
            self.data["opportunity_zone"] = self.find_intersects_one(self.data["geometry"], tables["oz"], "namelsad",
                                                                     parcel_proj=4326, zone_proj=4269)
            if self.data["zone"]:
                attr = {"geometry": self.data["geometry"],
                        "area": self.data["lot_area"],
                        "transit_priority": self.data["transit_priority"]
                        }
                zone_query = SanDiegoZoneQuery()
                zone_info = zone_query.get(self.data["zone"], attr)
                if zone_info['reference']:
                    self.data["use_regulations"] = zone_info['use_regulations']
                    self.data["dwelling_units"] = zone_info['dwelling_units']
                    self.data["buildable_area"] = zone_info['buildable_area']
                    self.data["max_dwelling_units"] = self.data["dwelling_units"][-1]['value']
                    self.data["max_buildable_area"] = self.data["buildable_area"][-1]['value']

        return self.data