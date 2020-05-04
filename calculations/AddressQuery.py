from shapely.geometry import shape
import re
import simplejson as json
import database as db

FT_PER_M = 3.280839895 #for sq ft per sq m, square this value

def area(geometry:dict):
    """returns the area of the geospatial data geometry"""
    return shape(geometry).area

def match_search(string, search, in_order=True):
    """true if search matches string"""
    search = re.sub(r'\W+', ' ', search).lower().strip()
    string = re.sub(r'\W+', ' ', string).lower().strip()
    if search == string:
        return True
    else:
        for s in search.split(' '):
            if s not in string:
                return False
            else:
                if in_order:
                    string = string.replace(s, '\t').split('\t')[-1]
        return True

"""
An abstract class for querying an Address.
All instances of AddressQuery's subclasses should be handled via AddressQueryFactory
"""
class AddressQuery:
    tables = {}
    city_list = ()
    def __init__(self):
        """This default constructor should not be overridden."""
        self.conn = db.init_conn()
        self.cur = self.conn.cursor()
        self.data = {
            "geometry": None, #dict (geojson)
            "apn": None, #str
            "street_address": None, #str
            "city": None, #str
            "state": None, #str
            "zip": None, #str
            "owner_name": None, #str
            "owner_address": None, #stt
            "lot_area": None, #float
            "lot_width": None, #float
            "transit_priority": None, #boolean
            "opportunity_zone": None, #boolean
            "zone": None, #str
            "use_regulations": None, #dict
            "max_dwelling_units": None, #int
            "dwelling_units": None, #list[dict]
            "max_buildable_area": None, #float
            "buildable_area": None, #list[dict]
            "assessor_map_link": None, #str (url)
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
    def find_intersects_all(self, parcel_geometry:dict, zone_table, id_field, geom_field="geometry",
                         parcel_proj=None, zone_proj=None)->dict:
        """
        Iterates through all the entries of zone_table to see if its geometry intersects parcel_geometry
        :param parcel_geometry: geospatial data as a dict
        :param zone_table: name of table containing zone info in the database
        :param id_field: name of field in zone_table that has the zone's name
        :param geom_field: name of field in zone_table containing a zone's geospatial data as geojson
            assumes "geometry" if not specified
        :param parcel_proj: CRS projection of parcel geometry. Only populate if different from zone's projection.
        :param zone_proj: CRS projection of zone geometry. Only populate if different from parcel's projection
        :return: a dictionary of {key=Zone name, value=ratio of parcel_geometry occupied}
        """
        if (parcel_proj is None and zone_proj is not None) or (parcel_proj is not None and zone_proj is None):
            raise ValueError("parcel_proj and zone_proj must both be inputted, or neither inputted.")

        if parcel_proj:
            parcel_json = json.dumps(self.st_transform(parcel_geometry, parcel_proj, zone_proj))
        else:
            parcel_json = json.dumps(parcel_geometry)

        query = """
            SELECT 
                z.{0}, 
                ST_Area(ST_Intersection(ST_GeomFromGeoJSON(z.{3}), ST_GeomFromGeoJSON('{2}'))) / 
                    ST_Area(ST_GeomFromGeoJSON('{2}'))
            FROM public.{1} z
            WHERE ST_Intersects(ST_GeomFromGeoJSON(z.{3}), ST_GeomFromGeoJSON('{2}'))
            """.format(id_field, zone_table, parcel_json, geom_field)

        self.cur.execute(query)
        overlap_entries = {}
        for z in self.cur:
            if z[0] not in overlap_entries.keys():
                overlap_entries[z[0]] = z[1]
            else:
                overlap_entries[z[0]] += z[1]

        return overlap_entries

    def find_intersects_one(self, parcel_geometry:dict, zones_table:str, id_field, geom_field="geometry",
                         parcel_proj=None, zone_proj=None)->str:
        """
        :param parcel_geometry: geojson parcel polygon as dict
        :param zones_table: name of table containing zone info in the database
        :param id_field: name of field in zone_table that has the zone's name
        :param geom_field: name of field in zone_table containing a zone's geospatial data as geojson
            assumes "geometry" if not specified
        :param parcel_proj: CRS projection of parcel geometry. Only populate if different from zone's projection.
        :param zone_proj: CRS projection of zone geometry. Only populate if different from parcel's projection
        :return: The name of the zone as a str that overlaps the most with parcel_geometry
        """
        overlap_entries = self.find_intersects_all(parcel_geometry, zones_table, id_field, geom_field=geom_field,
                                                parcel_proj=parcel_proj, zone_proj=zone_proj)
        max_key = None
        max_value = 0
        for k, v in overlap_entries.items():
            if v > max_value:
                max_key = k
                max_value = v
        return max_key

    def find_intersects_many(self, parcel_geometry:dict, zones_table, id_field, min_ratio:float=0, geom_field="geometry",
                             parcel_proj=None, zone_proj=None)->dict:
        """
        :param parcel_geometry: geojson parcel polygon as dict
        :param zones_table: name of table containing zone info in the database
        :param id_field: name of field in zone_table that has the zone's name
        :param min_ratio: optional. minimum proportion of parcel_geometry required to returned
        :param geom_field: name of field in zone_table containing a zone's geospatial data as geojson
            assumes "geometry" if not specified
        :param parcel_proj: CRS projection of parcel geometry. Only populate if different from zone's projection.
        :param zone_proj: CRS projection of zone geometry. Only populate if different from parcel's projection
        :return: A dictionary containing all zones that occupy the min_ratio of parcel_geometry in the form
            { key = zone name, value = proportion of parcel occupied by zone }
        """
        overlap_entries = self.find_intersects_all(parcel_geometry, zones_table, id_field, geom_field=geom_field,
                                                   parcel_proj=parcel_proj, zone_proj=zone_proj)
        overlap_dict = {}
        if len(overlap_entries) > 0:
            for k, v in overlap_entries.items():
                if v >= min_ratio:
                    overlap_dict[k] = v
        return overlap_dict

    def st_transform(self, geometry:dict, in_proj=4326, out_proj=3857)->dict:
        """
        Uses the ST_TRANSFORM method in PostGIS to transform a GeoJSON object geometry
        :param geometry: geojson data as a dict to be transformed
        :param in_proj: epsg number (SRID) of geometry's current CRS projection; assumes 4326 if omitted
        :param out_proj: epsg number (SRID) of geometry's desired CRS projection; assumes 3857 if omitted
        """
        query = """
            SELECT ST_AsGeoJSON(ST_Transform(ST_GeomFromText(ST_AsText(ST_GeomFromGeoJSON('{0}')), {1}), {2}))
        """.format(json.dumps(geometry), str(in_proj), str(out_proj))
        self.cur.execute(query)

        return json.loads(self.cur.fetchone()[0])