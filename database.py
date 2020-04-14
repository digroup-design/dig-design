import simplejson as json
import psycopg2 as pg
from dig.settings import DATABASES

"""Handles the implementation of Postgres package psycopg2 for use in other modules"""

def _feature_to_dict(line:str)->dict:
    """checks if a line in a geojson file is a feature to be entered into database"""
    e_sub = '"type": "Feature"'
    if e_sub.lower() in line.lower():
        return json.loads(line.strip().rstrip(','))
    else:
        return {}

def init_conn():
    """Creates a connection with the SQL database, returning the connection object"""
    postgres = DATABASES['query']
    return pg.connect(host=postgres['HOST'], database=postgres['NAME'], user=postgres['USER'],
                            password=postgres['PASSWORD'], port=postgres['PORT'])

def _copy_table(sql_table):
    """move table from one database to another"""

    postgres = DATABASES['default']
    pg_old = pg.connect(host=postgres['HOST'], database="DIG_geojson",
                              user=postgres['USER'], password=postgres['PASSWORD'],
                              port=postgres['PORT'])
    cur_old = pg_old.cursor()

    cur_old.execute("select * from {0} limit 0".format(sql_table))
    fields = [d[0] for d in cur_old.description]
    cur_old.execute("SELECT * FROM {0}".format(sql_table))
    pg_old.close()

    conn = init_conn()
    cur = conn.cursor()
    #create table in new database
    cur.execute("CREATE TABLE public.{0}({1} int PRIMARY KEY)".format(sql_table, 'id'))
    for r in cur_old:
        entry = dict(zip(fields, r))
        pg_insert_one(sql_table, entry)
        cur.execute("COMMIT;")
    conn.close()

def pg_get_fields(sql_table, fields:list=None, cursor=None)->dict:
    """
    Returns a dictionary of fields of sql_table from a Postgres database
    :param sql_table: name of sql_table
    :param fields: optional. specifies a specific list of fields to be returned. each entry is assumed to already
        be present in sql_table. gets all fields if omitted
    :param cursor: connection cursor to use
    :return: Dictionary of fields in the format { key = field name : value = field data type }
    """
    if cursor:
        conn = None
    else:
        conn = init_conn()
        cursor = conn.cursor()

    if not fields:
        cursor.execute("select * from {0} limit 0".format(sql_table))
        fields = [d[0] for d in cursor.description]

    fields_type = {}
    if fields:
        type_query = ",".join(["pg_typeof({0})".format(f) for f in fields])
        query = "select {0} from {1}".format(type_query, sql_table)
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            fields_type = dict(zip(fields, result))
        else: #result can be none if table has 0 entries
            fields_type = {}
            for f in fields:
                fields_type[f] = "None"

    if conn: conn.close()
    return fields_type


def pyval_to_sql(val)->str:
    """:returns a variable val in Python to a string for a sql query"""

    if val is None: return "NULL"
    elif isinstance(val, str): return "'{0}'".format(val.replace("'", "''"))
    elif isinstance(val, dict): return "'{0}'".format(json.dumps(val).replace("'", "''"))
    # elif val.__class__ in [list, tuple, set]:
    #     val = tuple(val)
    #     TODO
    else: return str(val)

def pytype_to_sql(val)->str:
    """
    :param val: a value whose type is converted to a postgreSQL datatype or
        if val is of class type, it will be directly converted to a postgreSQL datatype
    :returns a str represenation of val's datatype for SQL"""
    data_map = {
        int: "INT",
        float: "DOUBLE PRECISION",
        bool: "BOOL",
        dict: "json",
        None.__class__: "VARCHAR(1)"}

    if val.__class__ in [list, tuple, set]:
        val = tuple(val)
        if len(val) == 0:
            return data_map[None.__class__] + "[]"
        else:
            list_type_set = set([elem.__class__ for elem in val])
            #TODO: edge case for empty tuple () -- elem to the first value that is not (), assume None if all ()
            if len(list_type_set) == 1:
                elem = val[0]
            else:
                elem = str(val[0])
            return pytype_to_sql(elem) + "[]"
    elif val.__class__ is not type:
        return pytype_to_sql(val.__class__)
    elif val in data_map.keys():
        return data_map[val]
    else:
        return "TEXT"

def pg_insert_one(sql_table, entry:dict, data_types=None, cursor=None)->bool:
    """
    :param sql_table: name of sql_table to be inputted into
    :param entry: dictionary representation of each entry stored as { key=field name, value }
    :param data_types: optional field that, if inputted accurately, improves performance by not needing to
        repeatedly call pg_get_fields. Will call pg_get_fields if omitted. Data_types should not be omitted if doing a
        large, repeated call of pg_insert_one. Needlessly redefining data_types slows down the query
    :param cursor: optional field to specify the use of any existing cursor. new connection will be made if not specified
    :return True if a change in columns was made, False if otherwise. The outside loop calling pg_insert_one will
    then know to only re-run pg_get_fields (input value for data_types) if a change in columns was made
    """

    if cursor:
        conn = None
        cur = cursor
    else:
        conn = init_conn()
        cur = conn.cursor()
    #make sure all fields in dict are inside sql_table
    if data_types is None:
        data_types = pg_get_fields(sql_table, cursor=cursor)

    column_change = False
    for f, v in entry.items():
        if f.lower() not in [k.lower() for k in data_types.keys()]:
            data_type = pytype_to_sql(v)
            cur.execute("ALTER TABLE {0} ADD {1} {2};".format(sql_table, f.lower(), data_type))
            column_change = True
        elif isinstance(v, str) and "CHAR" in data_types[f.lower()].upper():
            data_type = "TEXT"  # "VARCHAR({0})".format(str(len(v)))
            cur.execute("ALTER TABLE {0} ALTER COLUMN {1} TYPE {2} USING {1}::{2}".format(sql_table, f, data_type))
            column_change = True
        elif v is not None and "CHAR" in data_types[f.lower()].upper():
            data_type = pytype_to_sql(v)
            cur.execute("ALTER TABLE {0} ALTER COLUMN {1} TYPE {2} USING {1}::{2}".format(sql_table, f, data_type))
            column_change = True

    insert = "insert into {0} ({1}) values ({2});".format(sql_table,
                                                          ",".join([f for f in entry.keys()]),
                                                          ",".join([pyval_to_sql(v) for v in entry.values()]))
    cur.execute(insert)
    if conn: conn.close()

    return column_change

def geojson_to_pg(geojson, sql_table:str):
    """
    Takes a geojson file geojson and uploads it into a new sql_table
    :param geojson: name of geojson file, including extension *.geojson
    :param sql_table: name of sql_table. must not already exist
    """
    conn = init_conn()
    cur = conn.cursor()

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
            column_change = pg_insert_one(sql_table, feature_dict, data_types, cursor=cur)
            cur.execute("COMMIT;")
            if column_change: data_types = pg_get_fields(sql_table)
        i += 1
        print("Progress: {0} / {1}".format(i, num_lines))
    conn.close()

def _sql_to_dict(values, fields, sql_table):
    """helper function to convert SELECT return statements into dict"""

    fields_type = pg_get_fields(sql_table, fields)
    result_dict = {}
    for val, (f, ty) in zip(values, fields_type.items()):
        result_dict[f] = val
    return result_dict