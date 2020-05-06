from calculations.SanDiegoZoneQuery import SanDiegoZoneQuery
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
zone="CN-1-2"
attr = {
    "area": 17751.11,
    "transit_priority": True
}

zone="CUPD-CU-1-1"
attr = {
    "area": 17751.11,
    "transit_priority": True
}

q = SanDiegoZoneQuery()
data = q.get(zone, attr)
print(q)