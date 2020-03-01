from shapely.geometry import Polygon, MultiPolygon, mapping, shape
import calculations.GLOBALS as GLOBALS
import simplejson as json
from django.db.models.functions import Concat, Replace
from django.db.models import Value as V
import dig.models as models

class GisDB:
    def __init__(self, name):
        self.name = name
        GLOBALS.db_dict[self.name] = self
        self._init_models()

    def _init_models(self):
        self.zone_model = models.Zone
        self.address_model = models.Address
        self.parcel_model = models.Parcel

    def get_address_feature(self, street_str, address_model=None):
        if address_model is None:
            address_model = self.address_model
        full_address = Replace(Concat('number', V(' '), 'street_name', V(' '), 'street_sfx'), V('  '), V(' '))
        address_set = address_model.objects.annotate(full_address=full_address)
        query = address_set.filter(full_address__iexact=street_str)
        if len(query) > 0:
            return query[0]
        else:
            return None

    def get_geometry(self, feature):
        return json.loads(feature.geometry.replace('\'', '\"'))

    #input an address object
    #returns a string tuple for address proper
    def get_address_proper(self, address_feature):
        first_line = ' '.join([str(s).title() for s in [address_feature.number, address_feature.street_name,
                                                        address_feature.street_sfx, address_feature.unit] if s is not None])
        second_line = ' '.join([s for s in [address_feature.city, address_feature.state,
                                            address_feature.zip] if s is not None])
        return first_line, second_line

    def get_parcel_feature(self, parcel_id, parcel_model=None):
        if parcel_model is None:
            parcel_model = self.parcel_model
        query = parcel_model.objects.filter(parcel_id=parcel_id)
        if len(query) > 0:
            return query[0]
        else:
            return None

    def address_to_zone(self, street_str, address_model=None, parcel_model=None, zone_model=None):
        if address_model is None:
            address_model = self.address_model
        if zone_model is None:
            zone_model = self.zone_model
        if parcel_model is None:
            parcel_model = self.parcel_model

        address_feature = self.get_address_feature(street_str, address_model=address_model)
        parcel_id = address_feature.parcel_id
        print("{0} found with Parcel ID: {1}".format(address_feature, parcel_id))
        parcel_feature = self.get_parcel_feature(parcel_id, parcel_model=parcel_model)
        parcel_geometry = self.get_geometry(parcel_feature)
        return self.get_zone(parcel_geometry, zone_model=zone_model)


    #if one_zone, return only a single string representing the zone that covers the most area
    #if one_zone is false, returns a list of strings representing the zones
    def get_zone(self, parcel_feature, one_zone=True, threshold=0.01, zone_model=None):
        if zone_model is None:
            zone_model = self.zone_model
        lot_polygon = shape(self.get_geometry(parcel_feature))
        zone_dict = {}
        for z in zone_model.objects.all():
            zone_polygon = shape(self.get_geometry(z))
            if zone_polygon.intersects(lot_polygon):
                if z.name not in zone_dict.keys():
                    zone_dict[z.name] = 0
                zone_dict[z.name] += zone_polygon.intersection(lot_polygon).area
        if zone_dict == {}:
            print("No zone found")
            return None
        else:
            if one_zone:
                max_zone = None
                max_area = 0
                for k, v in zone_dict.items():
                    if v > max_area:
                        max_zone = k
                        max_area = v
                return max_zone
            else:
                total_area = sum(zone_dict.values())
                return [z for z in zone_dict.keys() if (zone_dict[z]/total_area >= threshold)]

    def is_in_zone(self, parcel_feature, zone_name, zone_model=None):
        if zone_model is None:
            zone_model = self.zone_model
        lot_polygon = shape(self.get_geometry(parcel_feature))
        for z in zone_model.objects.filter(name=zone_name):
            zone_polygon = shape(self.get_geometry(z))
            if zone_polygon.intersects(lot_polygon):
                return True
        return False


