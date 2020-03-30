from shapely.geometry import Polygon, MultiPolygon, mapping, shape
from pyproj import Proj, Transformer, CRS
import database as db
import simplejson as json

FT_PER_M = 3.280839895 #for sqft per sq m, square this value
crs_4326 = CRS.from_epsg(4326)
crs_3857 = CRS.from_epsg(3857)
transformer = Transformer.from_crs(crs_4326, crs_4326)
x = -121.917877047225588
y = 37.377241996531545

#TODO: Work in progress
def transform_geometry(geometry:dict, transformer):
    geo = geometry.copy()
    def transform_coords(coords:list, transformer):
        if len(coords) == 0:
            return []
        elif isinstance(coords[0], float) or isinstance(coords[0], int):
            if len(coords) == 2:
                return transformer.transform(coords[0], coords[1])
            elif len(coords) == 3:
                return transformer.transform(coords[0], coords[1], coords[2])
            else:
                return transformer.transform(coords[0], coords[1], coords[2], coords[3])
        else:
            for i in range(0, len(coords)):
                coords[i] = transform_coords(coords[i], transformer)
            return coords

    geo["coordinates"] = transform_coords(geo["coordinates"], transformer)
    return geo

def test():
    parcel_feature = db.pg_find_one("sanjose_parcels", {})
    geometry = json.loads(str(parcel_feature["geometry"]).replace("'", '"'))
    geo_t = transform_geometry(geometry, transformer)
    print(geo_t)

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

#zones_query is assumed to be an iterable of dict items
def get_overlaps_all(parcel_geometry:dict, zone_table, id_field=None)->dict:
    parcel_shape = shape(parcel_geometry)
    parcel_area = parcel_shape.area
    fields = list(db.pg_get_fields(zone_table).keys())
    if id_field is None or id_field not in fields:
        if len(fields) > 1: id_field = fields[1]
        else: id_field = fields[0]
    id_idx = fields.index(id_field)
    geom_idx = fields.index("geometry")
    db.cur.execute("SELECT * FROM public.{0}".format(zone_table))

    overlap_entries = {}
    for z in db.cur:
        geom = shape(z[geom_idx])
        if parcel_shape.intersects(geom):
            if z[id_idx] not in overlap_entries.keys():
                overlap_entries[z[id_idx]] = {"data": [], "area": 0, "ratio": 0}
            overlap_entries[z[id_idx]]['data'].append(z)
            overlap_entries[z[id_idx]]['area'] += parcel_shape.intersection(geom).area
            overlap_entries[z[id_idx]]['ratio'] = overlap_entries[z[id_idx]]['area'] / parcel_area
    return overlap_entries

def get_overlaps_one(parcel_geometry:dict, zones_query, id_field=None)->str:
    overlap_entries = get_overlaps_all(parcel_geometry, zones_query, id_field)
    max_ratio = 0
    max_overlap = None
    for k, v in overlap_entries.items():
        if v["ratio"] > 0.5:
            return k
        elif o.ratio > max_ratio:
            max_overlap = k
    return max_overlap

def get_overlaps_many(parcel_geometry:dict, zones_query, id_field=None, min_ratio:float=0)->dict:
    overlap_entries = get_overlaps_all(parcel_geometry, zones_query, id_field)
    overlap_dict = {}
    for k, v in overlap_entries.items():
        if v["ratio"] >= min_ratio:
            overlap_dict[k] = v["ratio"]
    return overlap_dict


