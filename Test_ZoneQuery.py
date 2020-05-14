from calculations.San_Diego.SanDiegoZoneFactory import SanDiegoZoneFactory as F
# import re
# k = "Maximum permitted density(1)(2) (sf per DU)"
# print(re.match("max.* density", k.lower()))

#2405 union st
zone="RM-3-7"
attr = {
    "area": 4630,
    "transit_priority": True
}

#3901 clairemont dr
# zone="CN-1-2"
# attr = {
#     "area": 17751.11,
#     "transit_priority": True
# }
#
# zone="CU-1-1"
# attr = {
#     "area": 17751.11,
#     "transit_priority": True
# }

# q = F()
# data = q.get(zone, area = attr["area"], transit_priority=attr["transit_priority"])
# print(data)

def print_dict(dict_entry, tabs=0):
    for k, v in dict_entry.items():
        if v.__class__ is dict:
            print('\t' * tabs, k)
            print_dict(v, tabs + 1)
        else:
            print('\t' * tabs, k, v)

from calculations.AddressQueryFactory import AddressQueryFactory as Q
q = Q()
print_dict(q.get(city="San Diego", state="CA", address="2405 union st"))