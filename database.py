import simplejson as json
import psycopg2 as pg
import numpy as np
import os
import re
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
    elif val.__class__ in (dict, list, tuple, set):
        if val.__class__ == set: val = tuple(val)
        ret_str = json.dumps(val).replace("'", "''")
        replacements = (
            ('-Infinity', '"-INF"'),
            ('Infinity', '"INF"'),
            ('""-Infinity""', '"-INF"'),
            ('""Infinity""', '"INF"')
        )
        for r in replacements:
            ret_str = ret_str.replace(r[0], r[1])
        return "'{0}'".format(ret_str)
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
        set: "json",
        list: "json",
        tuple: "json",
        None.__class__: "VARCHAR(1)"
    }

    if val.__class__ is not type:
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


def _import_data(file_dir, transpose=False):
    """
    Imports zoning data from local tsv resources into memory as dictionaries, then loads them into SQL
    The first row of the tsv/csv files should be the names of the zones, and the first column should have
    the regulation labels. If the reverse if the case, set transpose=True

    All filenames, located within file_dir, follow the following format:
        [FOOT]_[D/U]_[Zone regex].tsv
        D for development regulations; U for use regulations
        'FOOT' is prefixed to the filename only if it contains footnote information for its respective file
    """

    def _str_to_num(text):
        text_clean = ''.join([c for c in text if (c == '.' or c.isalnum())])
        try:
            if "." in text_clean:
                return float(text_clean)
            elif text_clean.lower() in ('inf', '-inf'):
                return float(text_clean.lower())
            else:
                return int(text_clean)
        except ValueError:
            return text

    def _split_str(text, sep="[", strip="]"):
        text = text.replace(strip, "")
        return [t.strip() for t in text.split(sep)]

    def _format_dict(reg_dict):
        reg_dict_copy = {}
        # print("Format dict for ", reg_dict, reg_dict.keys())
        for zn, rule_dict in reg_dict.items():
            working_dict = {}
            for k, v in rule_dict.items():
                footnotes = _split_str(k, "[", "]")
                k = footnotes.pop(0)
                if "\\" in k:
                    key_parts = k.split("\\")
                    subcategory = key_parts[0]
                    label = key_parts[1]
                else:
                    subcategory = None
                    label = k

                rule_footnotes = _split_str(v, "(", ")")
                rule = _str_to_num(rule_footnotes.pop(0))
                footnotes += rule_footnotes

                if len(footnotes) == 0:
                    footnotes = None

                working_dict[label] = {
                    "rule": rule,
                    "subcategory": subcategory,
                    "footnotes": footnotes
                }
            reg_dict_copy[zn] = working_dict
        return reg_dict_copy

    use_regs = {}
    dev_regs = {}
    use_footnotes = {}
    dev_footnotes = {}

    def _genfromtxt(filename, delimiter='\t', encoding='utf-8'):
        array = []
        for r in open(filename, 'r', encoding=encoding):
            entry = r.strip('\n').split(delimiter)
            array.append(entry)
        return array

    for f in ['/'.join((file_dir, f)) for f in os.listdir(file_dir) if (f.endswith('.csv') or f.endswith('.tsv'))]:
        print(f)
        file_data = _genfromtxt(f, '\t', encoding='utf-8')
        if '/' in f:
            filename = str(f).split('/')[-1]
        else:
            filename = f
        filename = str(filename).split(".")[0]
        if transpose:
            file_data = np.transpose(file_data)

        # parse filename to see which dict to populate
        filename_parse = filename.split("_")
        data_dict = {}
        if filename_parse[0].upper() == "FOOT":  # case if file holds footnotes
            if len(filename_parse) < 3:
                raise ValueError("Filename for footnotes must be in format FOOT_[D/U]_[regex].[csv/tsv]")
            key = filename_parse[2].replace("+", ".+")
            for row in file_data:
                data_dict[row[0]] = row[1]
            if filename_parse[1].upper() == "D":
                dev_footnotes[key] = data_dict
            elif filename_parse[1].upper() == "U":
                use_footnotes[key] = data_dict
            else:
                raise ValueError("Filename for regulations must be in format [D/U]_[regex].[csv/tsv]")
        else:
            zone_keys = file_data[0]
            for i in range(1, len(zone_keys)):
                zone = zone_keys[i].replace("+", ".+")
                data_dict[zone] = {}
                for j in range(1, len(file_data)):
                    label = file_data[j][0]
                    data_dict[zone][label] = file_data[j][i]

            if filename_parse[0].upper() == "D":
                dev_regs.update(data_dict)
            elif filename_parse[0].upper() == "U":
                use_regs.update(data_dict)

    use_regs = _format_dict(use_regs)
    dev_regs = _format_dict(dev_regs)

    # insert footnotes entry to dicts use_regs and dev_regs
    for (foot_dict, reg_dict) in [(use_footnotes, use_regs), (dev_footnotes, dev_regs)]:
        for foot_key in foot_dict.keys():
            for reg_key in reg_dict.keys():
                if re.match(foot_key, reg_key):
                    reg_dict[reg_key]["footnotes"] = foot_dict[foot_key]

    # import files in folder tables
    tables = {}
    for f in ['/'.join((file_dir, 'tables', f)) for f in os.listdir(file_dir + '/tables')
              if (f.endswith('.csv') or f.endswith('.tsv'))]:
        table_parse = []
        for line in _genfromtxt(f):
            table_parse.append([_str_to_num(n) for n in line])
        tables[(f.split(".")[0]).split("/")[-1]] = table_parse

    conn = init_conn()
    cur = conn.cursor()
    def _iter_to_sql(sql_table, *items):
        values = [pyval_to_sql(itm) for itm in items]
        query = """
            INSERT INTO {0}
            VALUES ({1});
            COMMIT;
        """.format(sql_table, ", ".join(values))
        cur.execute(query)


    table_prefix = ''.join([c.lower() for c in (file_dir.split('/')[-1] if '/' in file_dir else file_dir) if c.isalnum()])
    dict_to_table = (
        (use_regs, "{0}_regulations_use".format(table_prefix)),
        (dev_regs, "{0}_regulations_dev".format(table_prefix)),
        (tables, "{0}_regulations_tables".format(table_prefix))
    )


    for n in dict_to_table:
        conn.rollback()
        for label, data in n[0].items():
            try:
                _iter_to_sql(n[1], label, data)
            except pg.errors.UniqueViolation:
                print("Updating existing name:", label)
                query = """
                    ROLLBACK;
                    UPDATE {0}
                    SET data = {1}
                    WHERE name = {2};
                    COMMIT;
                """.format(n[1], pyval_to_sql(data), pyval_to_sql(label))
                cur.execute(query)
    conn.close()
    return use_regs, dev_regs, tables