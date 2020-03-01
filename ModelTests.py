from django.db import models
import calculations.SanDiego as SanDiego
import django
django.setup() #remove this when not testing

san_diego_gis = SanDiego.san_diego_gis

# addr_string = "3215 46th st"
# address_feature = san_diego_gis.get_address_feature(addr_string)
# address_proper = san_diego_gis.get_address_proper(address_feature)
# print('\n'.join(address_proper))
# parcel_id = address_feature.parcel_id
#
# #parcel_id = '47911'
# print('Parcel ID: ' + parcel_id)
# parcel_feature = san_diego_gis.get_parcel_feature(parcel_id)
# print('Parcel found: ', parcel_feature)
# print(parcel_feature.geometry)
# zone = san_diego_gis.get_zone(parcel_feature)
# print('Zone: ', zone)

working_addresses = open("Uploaded_Addresses.txt", 'w')
for p in san_diego_gis.parcel_model.objects.all():
    parcel_id = p.parcel_id
    try:
        address_feature = san_diego_gis.address_model.objects.filter(parcel_id=parcel_id)[0]
        print(address_feature)
        working_addresses.write(str(address_feature) + '\n')
    except:
        pass
working_addresses.close()



