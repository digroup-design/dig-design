from shapely.geometry import Polygon, MultiPolygon, mapping, shape
from pyproj import Proj, Transformer, CRS, transform
import simplejson as json
import database as db
import copy

"""
An abstract class for querying an Address.
All instances of AddressQuery's subclasses should be handled via AddressQueryFactory
"""
class AddressQuery:
    def __init__(self):
        """This default constructor should not be overridden."""
        self.conn = db.init_conn()
        self.cur = self.conn.cursor()
        self.data = {
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

    def __del__(self):
        """This default destructor should not be overridden."""
        self.conn.close()

    def get(self, address=None, apn=None, city=None, state=None)->dict:
        """
        takes either address or apn and loads the data dict accordingly.
        :return data
        """
        raise NotImplementedError("Data fields to be populated: {0}".format(', '.join(list(self.data.keys()))))

    def __str__(self):
        if self.data["address"]:
            return self.data["address"]
        else:
            return "None"

    def get_fields(self, table_name:str):
        """returns a dictionary containing the {field_names: data_types} for table_name"""
        return db.pg_get_fields(table_name, cursor=self.cur)

#zones_query is assumed to be an iterable of dict items
    def get_overlaps_all(self, parcel_geometry:dict, zone_table, id_field, geom_field="geometry")->dict:
        """
        Iterates through all the entries of zone_table to see if its geometry intersects parcel_geometry
        :param parcel_geometry: geospatial data as a dict
        :param zone_table: name of table containing zone info in the database
        :param id_field: name of field in zone_table that has the zone's name
        :param geom_field: name of field in zone_table containing a zone's geospatial data as geojson
            assumes "geometry" if not specified
        :return: a dictionary of {key=Zone name, value=ratio of parcel_geometry occupied}
        """
        query = """
            SELECT 
                z.{0}, 
                ST_Area(ST_Intersection(ST_GeomFromGeoJSON(z.{3}), ST_GeomFromGeoJSON('{2}'))) / 
                    ST_Area(ST_GeomFromGeoJSON('{2}'))
            FROM public.{1} z
            WHERE ST_Intersects(ST_GeomFromGeoJSON(z.{3}), ST_GeomFromGeoJSON('{2}'))
            """.format(id_field, zone_table, json.dumps(parcel_geometry), geom_field)

        self.cur.execute(query)
        overlap_entries = {}
        for z in self.cur:
            if z[0] not in overlap_entries.keys():
                overlap_entries[z[0]] = z[1]
            else:
                overlap_entries[z[0]] += z[1]
        return overlap_entries

    def get_overlaps_one(self, parcel_geometry:dict, zones_table:str, id_field, geom_field="geometry")->str:
        """
        :param parcel_geometry: geojson parcel polygon as dict
        :param zones_table: name of table containing zone info in the database
        :param id_field: name of field in zone_table that has the zone's name
        :param geom_field: name of field in zone_table containing a zone's geospatial data as geojson
            assumes "geometry" if not specified
        :return: The name of the zone as a str that overlaps the most with parcel_geometry
        """
        overlap_entries = self.get_overlaps_all(parcel_geometry, zones_table, id_field, geom_field=geom_field)
        max_key = ''
        max_value = 0
        for k, v in overlap_entries.items():
            if v > max_value:
                max_key = k
                max_value = v
        return max_key


    def get_overlaps_many(self, parcel_geometry:dict, zones_table, id_field,
                          min_ratio:float=0, geom_field="geometry")->dict:
        """
        :param parcel_geometry: geojson parcel polygon as dict
        :param zones_table: name of table containing zone info in the database
        :param id_field: name of field in zone_table that has the zone's name
        :param min_ratio: optional. minimum proportion of parcel_geometry required to returned
        :param geom_field: name of field in zone_table containing a zone's geospatial data as geojson
            assumes "geometry" if not specified
        :return: A dictionary containing all zones that occupy the min_ratio of parcel_geometry in the form
            { key = zone name, value = proportion of parcel occupied by zone }
        """
        overlap_entries = self.get_overlaps_all(parcel_geometry, zones_table, id_field, geom_field=geom_field)
        overlap_dict = {}
        if len(overlap_entries) > 0:
            for k, v in overlap_entries.items():
                if v >= min_ratio:
                    overlap_dict[k] = v
        return overlap_dict

"""Helper functions that may be used throughout AddressQuery objects"""
FT_PER_M = 3.280839895 #for sqft per sq m, square this value

def transform_geometry(geometry:dict, in_proj='epsg:4326', out_proj='epsg:3857'):
    """
    :param geometry: dict format of geospatial data from geojson
    :param in_proj: current CRS of geometry
    :param out_proj: desired CRS to convert into
    :return: a version of geometry converted to out_proj
    """
    inproj = Proj(in_proj)
    outproj = Proj(out_proj)

    def transform_coords(coords:list):
        """Recursive function to project coordinates with an indeterminate layer of nested lists"""
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
    """returns the area of the geospatial data geometry"""
    return shape(geometry).area
