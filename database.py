import simplejson as json

#checks if a line in a geojson file is a feature to be entered into database
def _feature_to_dict(string):
    e_sub = '"type": "Feature"'
    if e_sub.lower() in string.lower():
        return json.loads(string.strip().rstrip(','))
    else:
        return None

"""
All functions here are related to MonboDB queries
Note: They are currently unused
"""
# from pymongo import MongoClient
# connect_string = "mongodb+srv://digdesign:<Diggit123>@cluster0-t0vfo.mongodb.net/test?retryWrites=true&w=majority"
# mongo = MongoClient(connect_string)
#
# def geojson_to_mongo(geojson, collection):
#     print("Importing {0}...".format(geojson))
#     num_lines = sum(1 for i in open(geojson, 'rb'))
#     i = 0
#     for line in open(geojson, "r"):
#         feature = _feature_to_dict(str(line))
#         if feature:
#             feature_dict = feature["properties"]
#             feature_dict["geometry"] = feature["geometry"]
#             collection.insert_one(feature_dict)
#             print("Progress: {0} / {1}".format(i, num_lines))
#         i += 1

"""
All functions here are related to postgres SQL queries
All sql_table names are assumed to be under public
"""

import psycopg2
postgres = {'NAME': 'geojson',
            'PASSWORD': 'WIrqJruyTSAC8QSIxpTY',
            'HOST': 'dig-geojson.cxuk6wwk5lsd.us-west-2.rds.amazonaws.com',
            'USER': 'postgres',
            'PORT': '5432'}
pg = psycopg2.connect(host=postgres['HOST'], database=postgres['NAME'],
                      user=postgres['USER'], password=postgres['PASSWORD'],
                      port=postgres['PORT'])
cur = pg.cursor()

#move table from one database to anot
def _copy_table(sql_table):
    pg_old = psycopg2.connect(host=postgres['HOST'], database="DIG_geojson",
                              user=postgres['USER'], password=postgres['PASSWORD'],
                              port=postgres['PORT'])
    cur_old = pg_old.cursor()

    cur_old.execute("select * from {0} limit 0".format(sql_table))
    fields = [d[0] for d in cur_old.description]
    cur_old.execute("SELECT * FROM {0}".format(sql_table))

    #create table in new database
    cur.execute("CREATE TABLE public.{0}({1} int PRIMARY KEY)".format(sql_table, 'id'))
    for r in cur_old:
        entry = dict(zip(fields, r))
        pg_insert_one(sql_table, entry)
        cur.execute("COMMIT;")


def pg_get_fields(sql_table, fields:list=None)->dict:
    if fields is None or len(fields) == 0:
        cur.execute("select * from {0} limit 0".format(sql_table))
        fields = [d[0] for d in cur.description]
    if len(fields) == 0:
        return {}
    else:
        type_query = ",".join(["pg_typeof({0})".format(f) for f in fields])
        query = "select {0} from {1}".format(type_query, sql_table)
        cur.execute(query)
        result = cur.fetchone()
        if result:
            fields_type = dict(zip(fields, result))
        else: #result can be none if table has 0 entries
            fields_type = {}
            for f in fields:
                fields_type[f] = "None"
        return fields_type
"""
Converts a variable in Python to a string for a sql query
"""
def _pyval_to_sql(val)->str:
    if val is None: return "NULL"
    elif isinstance(val, str): return "'{0}'".format(val.replace("'", "''"))
    elif isinstance(val, dict): return "'{0}'".format(json.dumps(val).replace("'", "''"))
    else: return str(val)

"""
data_types is an optional field that, if inputted accurately, improves performance by not needing to
repeatedly query pg_get_fields. 
Return: True if a change in columns was made, False if otherwise. The outside loop calling pg_insert_one will
then know to only re-run pg_get_fields (input value for data_types) if a change in columns was made
"""
def pg_insert_one(sql_table, entry:dict, data_types=None):
    def _py_to_sql_type(py_value):
        if py_value is None:
            return "VARCHAR(1)"  # trivially assume any optional fields is a string
        else:
            data_map = {chr: "TEXT",
                        str: "TEXT", #"VARCHAR({0})".format(len(str(py_value))),
                        int: "INT",
                        float: "DOUBLE PRECISION",
                        bool: "BOOL",
                        dict: "json",
                        list: "TEXT"}
            return data_map[py_value.__class__]

    #make sure all fields in dict are inside sql_table

    if data_types is None:
        """
        data_types should not be omitted if doing a large, repeated call of pg_insert_one.
        Needlessly redefining data_types slows down the query
        """
        data_types = pg_get_fields(sql_table)

    column_change = False
    for f, v in entry.items():
        if f.lower() not in [k.lower() for k in data_types.keys()]:
            data_type = _py_to_sql_type(v)
            cur.execute("ALTER TABLE {0} ADD {1} {2};".format(sql_table, f.lower(), data_type))
            column_change = True
        elif isinstance(v, str) and "CHAR" in data_types[f.lower()].upper():
            data_type = "TEXT"  # "VARCHAR({0})".format(str(len(v)))
            cur.execute("ALTER TABLE {0} ALTER COLUMN {1} TYPE {2} USING {1}::{2}".format(sql_table, f, data_type))
            column_change = True
        elif v is not None and "CHAR" in data_types[f.lower()].upper():
            data_type = _py_to_sql_type(v)
            cur.execute("ALTER TABLE {0} ALTER COLUMN {1} TYPE {2} USING {1}::{2}".format(sql_table, f, data_type))
            column_change = True

    insert = "insert into {0} ({1}) values ({2});".format(sql_table,
                                                          ",".join([f for f in entry.keys()]),
                                                          ",".join([_pyval_to_sql(v) for v in entry.values()]))
    cur.execute(insert)
    return column_change

def geojson_to_pg(geojson, sql_table:str):
    print("Importing {0}...".format(geojson))
    num_lines = sum(1 for i in open(geojson, 'rb'))
    i = 0
    cur.execute("CREATE TABLE public.{0}(ord int PRIMARY KEY);".format(sql_table))
    cur.execute("COMMIT;")
    data_types = pg_get_fields(sql_table)
    for line in open(geojson, "r"):
        feature = _feature_to_dict(str(line))
        if feature:
            feature_dict = feature["properties"]
            feature_dict["geometry"] = feature["geometry"]
            feature_dict["ord"] = i
            column_change = pg_insert_one(sql_table, feature_dict, data_types)
            cur.execute("COMMIT;")
            if column_change: data_types = pg_get_fields(sql_table)
        i += 1
        print("Progress: {0} / {1}".format(i, num_lines))

"""
Has cursor run the query 
"""
def _pg_and_equal(sql_table, query_dict:dict, tags:str = "", select_fields:list=None, limit:int=None):
    if query_dict == {}:
        cur.execute("SELECT * FROM public.{0}".format(sql_table))
    else:
        if select_fields: select_fields = ",".join(select_fields)
        else: select_fields = "*"
        if limit: limit = " LIMIT {0}".format(str(limit))
        else: limit = ""
        criteria_list = []
        for f, v in query_dict.items():
            if "i" in tags and isinstance(v, str):
                criteria_list.append("UPPER({0})=UPPER({1})".format(f, _pyval_to_sql(v)))
            else:
                criteria_list.append("{0}={1}".format(f, _pyval_to_sql(v)))
        criteria = " AND ".join(criteria_list)
        cur.execute("SELECT {0} FROM public.{1} WHERE {2}{3}".format(select_fields, sql_table, criteria, limit))

#helper function to convert SELECT return statements into dict
def _sql_to_dict(values, fields, sql_table):
    fields_type = pg_get_fields(sql_table, fields)
    result_dict = {}
    for val, (f, ty) in zip(values, fields_type.items()):
        result_dict[f] = val
    return result_dict


def pg_find_one(sql_table, query_dict:dict, tags:str = "", select_fields:list=None)->dict:
    if select_fields is None: select_fields = pg_get_fields(sql_table)
    _pg_and_equal(sql_table, query_dict, tags, select_fields=select_fields, limit=1)
    return _sql_to_dict(cur.fetchone(), select_fields, sql_table)

"""
To save memory, this function yields a dict item instead of returning an entire list.
To get the entire list in memory, use find_all
"""
def pg_find(sql_table, query_dict:dict, tags:str = "", select_fields:list=None)->dict:
    if select_fields is None:
        select_fields = pg_get_fields(sql_table)
    _pg_and_equal(sql_table, query_dict, tags)
    for result in cur.fetchall():
        yield _sql_to_dict(result, select_fields, sql_table)

def pg_find_all(sql_table, query_dict:dict, tags:str = "")->list:
    fields = pg_get_fields(sql_table)
    _pg_and_equal(sql_table, query_dict, tags)
    results = cur.fetchall()
    return [_sql_to_dict(r, fields, sql_table) for r in results]

"""
Returns one entry that satisfies the match of search_term to the concatenation of all listed fields
Will always be case insensitive
"""
def pg_concat_find_one(sql_table, search_term:str, fields:list, tags:str = "")->dict:
    search_term = _pyval_to_sql(search_term).strip()
    case_statement = "CONCAT_WS(' ', {0})".format(",".join(fields))
    if "i" in tags:
        case_statement = "UPPER({0})".format(case_statement)
        search_term = "UPPER({0})".format(search_term)
    select = "SELECT * FROM public.{0} WHERE {1} = {2} LIMIT 1".format(sql_table, case_statement, search_term)
    cur.execute(select)
    return cur.fetchone()