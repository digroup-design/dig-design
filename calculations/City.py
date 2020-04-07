from shapely.geometry import Polygon, MultiPolygon, mapping, shape
from pyproj import Proj, Transformer, CRS, transform
import database as db
import copy

FT_PER_M = 3.280839895 #for sqft per sq m, square this value

def transform_geometry(geometry:dict, in_proj='epsg:4326', out_proj='epsg:3857'):
    inproj = Proj(in_proj)
    outproj = Proj(out_proj)
    def transform_coords(coords:list):
        if len(coords) == 0:
            return []
        elif isinstance(coords[0], float) or isinstance(coords[0], int):
            if len(coords) == 2:
                return transform(inproj, outproj, coords[0], coords[1], always_xy=True)
            elif len(coords) == 3:
                return transform(inproj, outproj, coords[0], coords[1], coords[2], always_xy=True)
            else:
                return transform(inproj, outproj, coords[0], coords[1], coords[2], coords[3], always_xy=True)
        else:
            for i in range(0, len(coords)):
                coords[i] = transform_coords(coords[i])
            return coords

    geo = copy.deepcopy(geometry)
    geo["coordinates"] = transform_coords(geo["coordinates"])
    return geo

def area(geometry:dict):
    return shape(geometry).area

default_data = {
    "address": None, #may be built using street_number, street_name, street_sfx, city, etc
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
    "assessor_map": None,
    "geometry": None #geojson dict for parcel data
}

"""
An abstract class for querying an Address.
"""
class AddressQuery:
    def __init__(self):
        self.data = copy.deepcopy(default_data)
        self.conn = db.init_conn()
        self.cur = self.conn.cursor()

    def __del__(self):
        self.conn.close()

    def get(self, address=None, apn=None)->dict:
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
    def get_overlaps_all(self, parcel_geometry:dict, zone_table, id_field=None)->dict:
        parcel_shape = shape(parcel_geometry)
        parcel_area = parcel_shape.area
        fields = list(db.pg_get_fields(zone_table, cursor=self.cur).keys())
        if id_field is None or id_field not in fields:
            if len(fields) > 1: id_field = fields[1]
            else: id_field = fields[0]
        id_idx = fields.index(id_field)
        geom_idx = fields.index("geometry")
        self.cur.execute("SELECT * FROM public.{0}".format(zone_table))

        overlap_entries = {}
        for z in self.cur:
            geom = shape(z[geom_idx])
            #print(z[id_idx])  # DEBUG
            if parcel_shape.intersects(geom):
                if z[id_idx] not in overlap_entries.keys():
                    overlap_entries[z[id_idx]] = {"data": [], "area": 0, "ratio": 0}
                overlap_entries[z[id_idx]]['data'].append(z)
                overlap_entries[z[id_idx]]['area'] += parcel_shape.intersection(geom).area
                overlap_entries[z[id_idx]]['ratio'] = overlap_entries[z[id_idx]]['area'] / parcel_area
        return overlap_entries

    def get_overlaps_one(self, parcel_geometry:dict, zones_query, id_field=None)->str:
        overlap_entries = self.get_overlaps_all(parcel_geometry, zones_query, id_field)
        if len(overlap_entries) == 0: return None
        max_ratio = 0
        max_overlap = None
        for k, v in overlap_entries.items():
            if v["ratio"] > 0.5:
                return k
            elif v["ratio"] > max_ratio:
                max_overlap = k
        return max_overlap

    def get_overlaps_many(self, parcel_geometry:dict, zones_query, id_field=None, min_ratio:float=0)->dict:
        overlap_entries = self.get_overlaps_all(parcel_geometry, zones_query, id_field)
        if len(overlap_entries) == 0: return None
        overlap_dict = {}
        for k, v in overlap_entries.items():
            if v["ratio"] >= min_ratio:
                overlap_dict[k] = v["ratio"]
        return overlap_dict


