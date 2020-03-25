"""
An abstract class for querying an Address.
"""
class AddressQuery:
    data = { "address": None, #may be built using street_number, street_name, street_sfx, city, etc
             "street_number": None,
             "street_name": None,
             "street_sfx": None,
             "street_name_full": None,
             "city": None,
             "state": None,
             "zip": None,
             "city_zip": None,
             "apn": None,
             "parcel_id": None,
             "owner_name": None,
             "owner_address": None,
             "zone": None,
             "zone_info_dict": None, #dictionary containing all info pertaining to zone codes
             "lot_area": None,
             "lot_width": None,
             "max_density": None,
             "max_density_unit": None,
             "base_dwelling_units": None,
             "max_dwelling_units": None,
             "dwelling_area_dict": None, #dict containing FAR-related values and calculations
             "base_buildable_area": None,
             "affordable_dict": None, #dictionary containing affording housing calculations
             "transit_priority": None, #boolean
             "geometry": None #geojson dict for parcel data
            }

    def get(self, street_address=None, apn=None)->dict:
        """
        takes either address or apn and loads the data dict accordingly,
        :return data
        """
        raise NotImplementedError("Data fields to be populated: {0}".format(', '.join(list(self.data.keys()))))

    def __str__(self):
        if self.data["address"]:
            return self.data["address"]
        else:
            return "N/A"
