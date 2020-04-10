from time import time

import calculations.SanDiego as SanDiego
import calculations.SantaClara_County as SantaClara_County
import calculations.SanJose as SanJose

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

    #assumes sfx can only show up from index[2] onward. index[0] is house nmbr, index[1] is st name
    if len(address_parts) < 3:
        return address_parts.upper().strip()
    for i in range(1, len(address_parts)-1):
        p = address_parts[-i]
        if p in street_sfx_dict.keys():
            address_parts[-i] = street_sfx_dict[p][0]
            break
    return ' '.join(address_parts)


class AddressQueryFactory:
    def __init__(self, max_cache=120):
        """AddressQueueFactory will log data regarding address_queries. This is mainly intended for backend testing."""

        if type(max_cache) not in [int, float]:
            raise TypeError("max_cache must be an integer at least 1")
        if max_cache < 1:
            raise ValueError("max_cache must be an integer at least 1")

        self.max_cache = max_cache
        self.cache = []
        self.log = []

    def _update_log(self, log_entry, cache_entry):
        if len(self.log) == self.max_cache:
            self.cache.pop(0)
            self.log.pop(0)

        self.log.append(log_entry)
        self.cache.append(cache_entry)

    def get(self, city, state, address=None, apn=None):
        if address is None and apn is None:
            raise TypeError("Query requires either address or apn")

        address_query = None
        if state.lower() in ["ca", "california"]:
            if city.lower() in SanDiego.city_list:
                address_query = SanDiego.SanDiego()
            elif city.lower() == "san jose":
                address_query = SanJose.SanJose()
            elif city.upper() in SantaClara_County.city_list:
                address_query = SantaClara_County.SantaClara_County()

        data = {}
        if address_query:
            start_time = time()
            if address:
                data = address_query.get(address=_format_sfx(address))
                if data["geometry"] is None:
                    data = address_query.get(address=address)
            elif apn:
                data = address_query.get(apn=apn)
            end_time = time()
            self._update_log('{1} query for "{2}" in {0} s'.format(str(end_time - start_time),
                                                                   "Address" if address else "APN",
                                                                   address if address else apn), data)
        return data

    def __str__(self):
        if len(self.log) < 1:
            return "None"
        else:
            return self.log[-1]
