from time import time
from calculations.SanDiego import SanDiego
from calculations.SantaClara_County import SantaClara_County
from calculations.SanJose import SanJose

"""This module implements a Factory Pattern class to handle all instances of the many AddressQuery subclasses"""

def _init_street_sfx_dict(filename="calculations/street_sfx.csv"):
    street_sfx = {}
    with open(filename, 'r') as f:
        for line in f:
            entries = line.strip().split(',')
            street_sfx[entries[0]] = (entries[1], entries[2])
    return street_sfx
street_sfx_dict = _init_street_sfx_dict()

def _format_sfx(address_entry):
    """converts the address suffix into the Postal Service Standard Suffix Abbreviation"""
    address_parts = address_entry.upper().strip().split(' ')

    #assumes sfx can only show up from index[2] onward. index[0] is house number, index[1] is street name
    if len(address_parts) < 3:
        return address_entry.upper().strip()
    for i in range(1, len(address_parts)-1):
        p = address_parts[-i]
        if p in street_sfx_dict.keys():
            address_parts[-i] = street_sfx_dict[p][0]
            break
    return ' '.join(address_parts)

def _format_apn(apn_entry):
    """Strips all non-alphanumeric character for a string. Used to format APN texts."""
    return ''.join([c for c in apn_entry if c.isalnum()])

class AddressQueryFactory:
    queries = (
        (("ca", "california"), (SanJose, SanDiego, SantaClara_County)),
    )

    def __init__(self, max_cache=120):
        """AddressQueueFactory will log data from address_queries. This is mainly intended for backend testing."""
        if type(max_cache) not in [int, float]:
            raise TypeError("max_cache must be an integer at least 1")
        if max_cache < 1:
            raise ValueError("max_cache must be an integer at least 1")

        self.max_cache = max_cache
        self.cache = []
        self.log = []

    def get(self, city, state, address=None, apn=None):
        """
        factory method for returning data using get() from various AddressQuery subclasses, depending on inputs
        for city and state
        """
        if address is None and apn is None:
            raise TypeError("Query requires either address or apn")

        def _get_address_query():
            for query_entry in AddressQueryFactory.queries:
                if state.lower() in query_entry[0]:
                    for q in query_entry[1]:
                        if city.lower() in [c.lower() for c in q.city_list]:
                            return q()
            return None

        address_query = _get_address_query()

        data = {}
        if address_query:
            start_time = time()
            if address:
                address = address.replace("'", "''")
                data = address_query.get(address=_format_sfx(address))
                if data["geometry"] is None:
                    data = address_query.get(address=address)
            elif apn:
                apn = apn.replace("'", "''")
                data = address_query.get(apn=_format_apn(apn))
                if data["geometry"] is None:
                    data = address_query.get(apn=apn)
            end_time = time()
            self._update_log('{1} query for "{2}" in {0} s'.format(str(end_time - start_time),
                                                                   "Address" if address else "APN",
                                                                   address if address else apn), data)
        return data

    def __str__(self):
        """printing an instance will show the last log entry"""
        if len(self.log) < 1:
            return "None"
        else:
            return self.log[-1]

    def _update_log(self, log_entry, cache_entry):
        if len(self.log) == self.max_cache:
            self.cache.pop(0)
            self.log.pop(0)

        self.log.append(log_entry)
        self.cache.append(cache_entry)
