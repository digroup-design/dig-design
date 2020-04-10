from time import time

import calculations.SanDiego as SanDiego
import calculations.SantaClara_County as SantaClara_County
import calculations.SanJose as SanJose

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
            if address: data = address_query.get(address=address)
            elif apn: data = address_query.get(apn=apn)
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