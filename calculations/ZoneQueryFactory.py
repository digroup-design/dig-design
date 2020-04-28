from time import time
from calculations.SanDiego import SanDiegoZoneQuery
from calculations.SantaClara_County import *
from calculations.SanJose import *

"""This module implements a Factory Pattern class to handle all instances of the many ZoneQuery subclasses"""

class ZoneQueryFactory:
    city_map = {
        "san diego": SanDiegoZoneQuery
    }
    def __init__(self, max_cache=120):
        """AddressQueueFactory will log data from address_queries. This is mainly intended for backend testing."""
        if type(max_cache) not in [int, float]:
            raise TypeError("max_cache must be an integer at least 1")
        if max_cache < 1:
            raise ValueError("max_cache must be an integer at least 1")

        self.max_cache = max_cache
        self.cache = []
        self.log = []

    def get(self, city, zone, attr=None):
        """
        factory method for returning data using get() from various ZoneQuery subclasses
        """

        def _get_zone_query(city):
            return ZoneQueryFactory.city_map[city]

        zone_query = _get_zone_query(city)

        start_time = time()
        data = zone_query.get(zone, attr)
        end_time = time()
        self._update_log('{1} query for "{2}" in {0} s'.format(str(end_time - start_time),
                                                               "Zone", zone), data)
        return data

    def __str__(self):
        """printing an instance will show the last log entry"""
        if len(self.log) < 1:
            return "None"
        else:
            return self.log[-1]

    def _update_log(self, log_entry, cache_entry):
        if len(self.log) >= self.max_cache:
            self.cache.pop(0)
            self.log.pop(0)

        self.log.append(log_entry)
        self.cache.append(cache_entry)
