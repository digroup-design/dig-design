from pymongo import MongoClient
import psycopg2
import simplejson as json

connect_string = "mongodb+srv://digdesign:<Diggit123>@cluster0-t0vfo.mongodb.net/test?retryWrites=true&w=majority"
mongo = MongoClient(connect_string)

postgres = {'NAME': 'geojson',
            'PASSWORD': 'WIrqJruyTSAC8QSIxpTY',
            'HOST': 'dig-geojson.cxuk6wwk5lsd.us-west-2.rds.amazonaws.com',
            'USER': 'postgres',
            'PORT': '5432'}
pg = psycopg2.connect(host=postgres['HOST'], database=postgres['NAME'],
                      user=postgres['USER'], password=postgres['PASSWORD'],
                      port=postgres['PORT'])
cur = pg.cursor()

def _feature_to_dict(string):
    e_sub = '"type": "Feature"'
    if e_sub.lower() in string.lower():
        return json.loads(string.strip().rstrip(','))
    else:
        return None

def geojson_to_mongo(geojson, collection):
    print("Importing {0}...".format(geojson))
    num_lines = sum(1 for i in open(geojson, 'rb'))
    i = 0
    for line in open(geojson, "r"):
        feature = _feature_to_dict(str(line))
        if feature:
            feature_dict = feature["properties"]
            feature_dict["geometry"] = feature["geometry"]
            collection.insert_one(feature_dict)
            print("Progress: {0} / {1}".format(i, num_lines))
        i += 1

"""
All functions here are related to postgres SQL queries
All sql_table names are assumed to be under public
"""

def _pg_get_fields(sql_table)->list:
    cur.execute("select * from {0} limit 0".format(sql_table))
    return [d[0] for d in cur.description]

"""
Converts a variable in Python to a string for a sql query
"""
def _pyval_to_sql(val):
    if val is None: return "NULL"
    elif isinstance(val, str): return "'{0}'".format(val.replace("'", "''"))
    elif isinstance(val, dict): return "'{0}'".format(json.dumps(val).replace("'", "''"))
    else: return str(val)

"""
data_type is a required input that must state all {<field names>: <field data types>}
data_types should include exactly whichever fields are already in the table, and will be updated and returned if new
fields are added
"""
def pg_insert_one(sql_table, entry:dict, data_types:dict):
    def _py_to_sql_type(py_value):
        if py_value is None:
            return "VARCHAR(1)"  # trivially assume any optional fields is a string
        else:
            data_map = {chr: "CHAR(1)",
                        str: "VARCHAR({0})".format(len(str(py_value))),
                        int: "INT",
                        float: "DOUBLE PRECISION",
                        bool: "BOOL",
                        dict: "json"}
            return data_map[py_value.__class__]

    #make sure all fields in dict are inside sql_table
    for f, v in entry.items():
        if f not in data_types.keys():
            data_types[f] = _py_to_sql_type(v)
            cur.execute("ALTER TABLE {0} ADD {1} {2};".format(sql_table, f, data_types[f]))
        if isinstance(v, str):
            field_len = int(data_types[f].rstrip(')').split("(")[1])
            if len(v) > field_len:
                data_types[f] = "VARCHAR({0})".format(str(len(v)))
                cur.execute("ALTER TABLE {0} ALTER COLUMN {1} TYPE {2}".format(sql_table, f, data_types[f]))
        elif v is not None and data_types[f].upper().startswith("VARCHAR"):
            data_types[f] = _py_to_sql_type(v)
            cur.execute("ALTER TABLE {0} ALTER COLUMN {1} TYPE {2} USING {1}::{2}".format(sql_table, f, data_types[f]))

    insert = "insert into {0} ({1}) values ({2});".format(sql_table,
                                                          ",".join([f for f in entry.keys()]),
                                                          ",".join([_pyval_to_sql(v) for v in entry.values()]))
    cur.execute(insert)
    return data_types

def geojson_to_pg(geojson, sql_table:str):
    print("Importing {0}...".format(geojson))
    num_lines = sum(1 for i in open(geojson, 'rb'))
    i = 0
    cur.execute("CREATE TABLE public.{0}(ord int PRIMARY KEY);".format(sql_table))
    data_types = {"ord": "INT"}
    for line in open(geojson, "r"):
        feature = _feature_to_dict(str(line))
        if feature:
            feature_dict = feature["properties"]
            feature_dict["geometry"] = feature["geometry"]
            feature_dict["ord"] = i
            data_types = pg_insert_one(sql_table, feature_dict, data_types)
            cur.execute("COMMIT;")
        i += 1
        print("Progress: {0} / {1}".format(i, num_lines))

"""
Has cursor run the query 
"""
def _pg_and_equal(sql_table, query_dict:dict, tags:str = ""):
    criteria_list = []
    for f, v in query_dict.items():
        if "i" in tags:
            criteria_list.append("lower({0})=lower({1})".format(f, _pyval_to_sql(v)))
        else:
            criteria_list.append("{0}={1}".format(f, _pyval_to_sql(v)))
    criteria = " AND ".join(criteria_list)
    if query_dict == {}:
        cur.execute("SELECT * FROM public.{0}".format(sql_table))
    else:
        cur.execute("SELECT * FROM public.{0} WHERE {1}".format(sql_table, criteria))

def pg_find_one(sql_table, query_dict:dict, tags:str = "")->dict:
    fields = _pg_get_fields(sql_table)
    _pg_and_equal(sql_table, query_dict, tags)
    result = cur.fetchone()
    result_dict = {}
    for i in range(0, len(result)):
        result_dict[fields[i]] = result[i]
    return result_dict

"""
To save memory, this function yields a dict item instead of returning an entire list.
To get the entire list in memory, use find_all
"""
def pg_find(sql_table, query_dict:dict, tags:str = "")->dict:
    fields = _pg_get_fields(sql_table)
    _pg_and_equal(sql_table, query_dict, tags)
    for result in cur.fetchall():
        result_dict = {}
        for i in range(0, len(result)):
            result_dict[fields[i]] = result[i]
        yield result_dict

def pg_find_all(sql_table, query_dict:dict, tags:str = "")->list:
    query_list = []
    fields = _pg_get_fields(sql_table)
    _pg_and_equal(sql_table, query_dict, tags)
    for result in cur.fetchall():
        result_dict = {}
        for i in range(0, len(result)):
            result_dict[fields[i]] = result[i]
        query_list.append(result_dict)
    return query_list

"""
Returns one entry that satisfies the match of search_term to the concatenation of all listed fields
Will always be case insensitive
"""
def pg_concat_find_one(sql_table, search_term:str, fields:list)->dict:

    "SELECT * FROM public.{0} WHERE CONCAT({1})={2} OR CONCAT({3})={4}"
    return {}

# uploads = {"sanjose_zones": "sanjose_zones.geojson",
#            "sanjose_addresses": "sanjose_address_points.geojson"}

# for db, geojson in uploads.items():
#      geojson_to_pg(geojson, db)



