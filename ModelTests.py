from django.db import models
import calculations.SanDiego as SanDiego

san_diego_gis = SanDiego.san_diego_gis

addr_string = "3215 46th st"
address_feature = san_diego_gis.get_address_feature(addr_string)
address_proper = san_diego_gis.get_address_proper(address_feature)
print('\n'.join(address_proper))
parcel_id = address_feature.parcel_id

#parcel_id = '47911'
print('Parcel ID: ' + parcel_id)
parcel_feature = san_diego_gis.get_parcel_feature(parcel_id)
print('Parcel found: ', parcel_feature)
print(parcel_feature.geometry)
zone = san_diego_gis.get_zone(parcel_feature)
print('Zone: ', zone)



