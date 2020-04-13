import database as db

"""This module is currently unfinished and not implemented"""
def autofill_list(entry:str, table:str, *fields:str):
    conn = db.init_conn()
    cur = conn.cursor()
    query = """
        SELECT {0} FROM public.{1} WHERE {3} LIKE UPPER('{2}%')
    """.format(','.join(fields), table, entry, fields[0])
    cur.execute(query)
    result = cur.fetchall()
    conn.close()
    return result


