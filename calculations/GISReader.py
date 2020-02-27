import os.path as path
import operator
import simplejson as json
from shapely.geometry import Polygon, MultiPolygon, mapping, shape
try:
    import calculations.GLOBALS as GLOBALS
except ModuleNotFoundError:
    import GLOBALS

db_dict = {}
ENTRY_SUBSTRING = '"type": "Feature"'

def geometry_to_polygon(geometry):
    return shape(geometry)

class GisDB:
    def __init__(self, name):
        self.name = name
        db_dict[self.name] = self

    def _get_geojson(self, filename):
        filename = '{0}/geojson/{1}.geojson'.format(self.name, filename)
        return GLOBALS.get_file(filename)

    def get_feature(self, geojson, *lookup, concat=False):
        if len(lookup) % 2 != 0:
            print("Lookup arguments must be in pairs (lookup_type, lookup_value).",\
                  "If concat is True, lookup_value can simply be '' for later outputs")
            return None

        return_feature = None
        file = self._get_geojson(geojson)
        for line in file:
            if ENTRY_SUBSTRING.lower() in line.lower():  # checks if line in geojson is a Feature entry
                feature = json.loads(line.strip().rstrip(','))
                properties = feature['properties']
                # iterates through all lookup parameters to ensure match
                if concat:
                    #this condition assumes the user is inputting an address
                    lookup_types = []
                    lookup_values = []
                    for a in range(0, len(lookup), 2):
                        lookup_types.append(lookup[a])
                        lookup_values.append(str(lookup[a+1]))

                    properties_values = [str(properties[t]) for t in lookup_types]

                    lookup_concat = ' '.join(filter(None, lookup_values))
                    properties_concat = (' '.join(filter(None, properties_values))).replace('.0 ', ' ')
                    if properties_concat.upper() == lookup_concat.upper():
                        return_feature = feature
                else:
                    for a in range(0, len(lookup), 2):
                        lookup_type = lookup[a].upper()
                        lookup_value = lookup[a + 1]
                        if type(lookup_value) == str:
                            lookup_value = lookup_value.upper()

                        if properties[lookup_type] == lookup_value:
                            return_feature = feature
                        else:
                            return_feature = None
                            break
                if return_feature is not None:
                    break
        return return_feature

    #input:
        #geojson - filename of geojson containing the information
        #return_type of the data to be searched - can be str or list of str
        #lookup - paired arguments of a lookup_type and a lookup_value
        #return - the return_type's value corresponding to the lookup
    def get_attr(self, geojson, return_type, *lookup, concat=False):
        feature = self.get_feature(geojson, *lookup, concat=concat)
        if feature is None:
            print('Lookup values not found.')
            return None
        else:
            properties = feature['properties']
            geometry = feature['geometry']
            if isinstance(return_type, list):
                return_value = []
                for r in return_type:
                    if r.lower() == "geometry":
                        return_value.append(geometry)
                    else:
                        return_value.append(properties[r])
            else:
                if return_type == 'geometry':
                    return_value = geometry
                else:
                    return_value = properties[return_type]
            return return_value

    #returns a dictionary of zones along with the area
    def get_zones_dict(self, geojson, lot_geometry, zone_label = "ZONE_NAME"):
        zones_dict = {}
        lot_polygon = shape(lot_geometry)
        file = self._get_geojson(geojson)
        for line in file:
            if ENTRY_SUBSTRING.lower() in line.lower(): #checks if line in geojson is a Feature entry
                feature = json.loads(line.strip().rstrip(','))
                geometry = feature['geometry']
                zone_polygon = shape(geometry)
                if lot_polygon.intersects(zone_polygon):
                    intersection_area = lot_polygon.intersection(zone_polygon).area
                    zone = feature['properties'][zone_label]
                    if zone in zones_dict.keys():
                        zones_dict[zone] += intersection_area
                    else:
                        zones_dict[zone] = intersection_area
        return zones_dict

    #if one_zone, return only a single string representing the zone that covers the most area
    #if one_zone is false, returns a list of strings representing the zones
    def get_zone(self, geojson, lot_geometry, zone_label="ZONE_NAME", one_zone=True, threshold = 0.01):
        zones_dict = self.get_zones_dict(geojson, lot_geometry, zone_label)
        total_area = sum(zones_dict.values())
        zones_dict_2 = {} #new dictionary to be copied into
        for k in zones_dict.keys():
            if zones_dict[k]/total_area >= threshold:
                zones_dict_2[k] = zones_dict[k]
        if one_zone:
            return max(zones_dict_2.items(), key=operator.itemgetter(1))[0]
        else:
            return [k for k in zones_dict_2.keys()]

    #returns true if lot_geometry interesects with any of the polygons in geojson
    def intersects_zone(self, geojson, lot_geometry):
        lot_polygon = shape(lot_geometry)
        file = self._get_geojson(geojson)
        for line in file:
            if ENTRY_SUBSTRING.lower() in line.lower():  # checks if line in geojson is a Feature entry
                feature = json.loads(line.strip().rstrip(','))
                zone_polygon = shape(feature['geometry'])
                if lot_polygon.intersects(zone_polygon):
                    return True
        return False
