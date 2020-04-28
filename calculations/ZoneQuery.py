from database import init_conn
import re
from shapely.geometry import shape

AC_PER_SF = 43560

def area(geometry:dict):
    return shape(geometry).area

class ZoneQuery:
    use_regs = None
    dev_regs = None
    tables = None
    initialized_data = False

    def __init__(self):
        self.conn = init_conn()
        self.cur = self.conn.cursor()
        self.data = {
            "zone": None,
            "desc": None,
            "reference": None,
            "use_regulations": None, #dict
            "dev_regulations": None, #dict
            #The following will all be stored as 2d arrays (tuples) where each row is (value, unit, notes, calculations)
            "far": None,
            "density": None,
            "buildable_area": None, #The following fields can be omitted if lot area not given
            "dwelling_units": None,
            "height": None,
            "lot_size": None,
            "lot_coverage": None
        }
        self.attr = None

    def __del__(self):
        self.conn.close()

    def __str__(self):
        string_parts = []
        for k, v in self.data.items():
            if v.__class__ == dict:
                string_parts.append(str(k) + ': ')
                for k2, v2 in v.items():
                    string_parts.append('\t' + str(k2) + ': ' + str(v2))
            elif v.__class__ in [set, list, tuple]:
                string_parts.append(k + ": ")
                for n in v:
                    string_parts.append('\t' + str(n))
            else:
                string_parts.append(k + ": " + str(v))
        return '\n'.join(string_parts)

    @staticmethod
    def _re_match(pattern, *string):
        """Returns True if pattern matches any of the string"""
        for s in string:
            if bool(re.match(pattern, s)): return True
        return False

    def _get_table(self, key, sql_table):
        """Retrieves a table in the form of json from a sql_table"""
        query = "SELECT data from {0} WHERE name = '{1}'".format(sql_table, key)
        self.cur.execute(query)
        return self.cur.fetchone()[0]

    def _find_regs(self, zone, sql_table):
        """
        Returns the data relevant for zone within sql_table, using regular expression checks.
        If no matches, returns None.
        """
        query = "SELECT data from {0} WHERE '{1}' ~ name".format(sql_table, zone)
        self.cur.execute(query)
        try:
            return self.cur.fetchone()[0]
        except:
            return None

    @staticmethod
    def _coalesce(*arg):
        """
        :param arg: an array of arg
        :return: first arg that is not None. Returns None as str if all is None
        """
        for a in arg:
            if a is not None:
                return a
        return 'None'

    @staticmethod
    def _ac_to_sf(ac_val):
        """
        :param ac_val: parcel area in acres
        :return: parcel area in square feet
        """
        return ac_val * AC_PER_SF

    @staticmethod
    def _sf_to_ac(sf_val):
        """
        :param sf_val: parcel area in square feet
        :return: parcel area in acres
        """
        return sf_val / AC_PER_SF

    @staticmethod
    def _isnumber(val):
        return val.__class__ in (int, float)

    @staticmethod
    def _makeentry(value=None, unit=None, note=None, calc=None):
        return {
            "value": value,
            "unit": unit,
            "note": note,
            "calc": calc
        }

    def get(self, zone:str, attr:dict=None):
        """
        This method is will populate the values for self.data and return it
        :param zone: the string name of the zone to match with what's in the database
        :param attr: a dict of attributes that may be relevant to zoning. The keys for an attr should be pre-defined
            and may differ between cities
        :return data: returns self.data, with relevant fields populated. If a numeric field may have multiple
            possibilities (due to an unspecified number of floors, unspecified transit_priority, etc), then list of
            tuples (value, condition, [notes]) should be outputted
        """
        raise NotImplementedError