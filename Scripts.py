#This module only exists to execute one-time scripts. Nothing here should be referenced in or executed any other modules.
import simplejson as json

#remember to include .geojson at the end!
def _get_geojson_dir(folder, filename):
    parent_dir = os.path.abspath(os.getcwd())
    return parent_dir + "\\data\\{0}\\geojson\\{1}".format(folder, filename)

#breaks up a large file into several small files based on their main lookup property
def break_file(folder, filename):
    filedir = _get_geojson_dir(folder, filename)
    file = open(filedir, 'r')

    subfiles = {}
    for i in range(1, 10):
        sub_filedir = filedir.replace('.geojson', '[{0}].geojson'.format(str(i)))
        subfiles[i] = open(sub_filedir, 'w')

    for line in file:
        if ENTRY_SUBSTRING.lower() in line.lower():  # checks if line in geojson is a Feature entry
            feature = json.loads(line.strip().rstrip(','))
            properties = feature['properties']
            parcel_id = str(properties['PARCELID'])
            file_id = int(parcel_id[0])
            subfiles[file_id].write(line)
            print("{0} wrote to file #{1}".format(parcel_id, file_id))

    file.close()
    for f in subfiles.values(): f.close()

#break_file('San Diego', 'Parcels.geojson')

from django.db import models
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dig.settings')
import django
django.setup()
import dig.models as models

ENTRY_SUBSTRING = '"type": "Feature"'

def geojson_to_zone():
    file = open('../data/San Diego/geojson/ZONING_BASE_SD.geojson')
    for line in file:
        if ENTRY_SUBSTRING.lower() in line.lower():  # checks if line in geojson is a Feature entry
            feature = json.loads(line.strip().rstrip(','))
            geometry = feature['geometry']
            name = feature['properties']['ZONE_NAME']
            date = feature['properties']['IMP_DATE']
            model = models.SanDiego_Zone(name=name, imp_date=date, geometry=geometry)
            print(model)
            model.save()

def geojson_to_address():
    file = open('../data/San Diego/geojson/Address_APN_v2.geojson')
    i = 0
    log = []
    for line in file:
        if ENTRY_SUBSTRING.lower() in line.lower():  # checks if line in geojson is a Feature entry
            feature = json.loads(line.strip().rstrip(','))
            number = str(feature['properties']['ADDRNMBR']).replace('.0', '')
            unit = feature['properties']['ADDRUNIT']
            street_name = feature['properties']['ADDRNAME']
            street_sfx = feature['properties']['ADDRSFX']
            city = feature['properties']['COMMUNITY']
            zip = feature['properties']['ADDRZIP']
            state = feature['properties']['STATE']
            apn = feature['properties']['APN']
            parcel_id = feature['properties']['PARCELID']
            model = models.SanDiego_Address(number=number, unit=unit, street_name=street_name, street_sfx=street_sfx,\
                                            city=city, state=state, zip=zip, apn=apn, parcel_id=parcel_id)
            try:
                model.save()
                print('{0}: {1}'.format(i, model))
            except:
                log.append("{0}: {1}".format(i, feature))
                print('{0}: {1} -- Error found'.format(i, model))
            i += 1
    if len(log) > 0:
        print("Errors written to error_logs.txt")
        with open('error_logs.txt', 'w') as error_log:
            for l in log:
                error_log.write(l + '\n')
            error_log.close()
    else:
        print("Done. No errors found.")
geojson_to_address()

def geojson_to_parcel():
    file_dir = '../data/San Diego/geojson/Parcels.geojson'
    num_lines = sum(1 for i in open(file_dir, 'rb'))
    i = 0
    error_log = open('Parcels_log.txt', 'w')
    file = open(file_dir, 'r')
    for line in file:
        if ENTRY_SUBSTRING.lower() in line.lower():  # checks if line in geojson is a Feature entry
            feature = json.loads(line.strip().rstrip(','))
            parcel_id = feature['properties']['PARCELID']
            apn = feature['properties']['APN']
            owner1 = feature['properties']['OWN_NAME1']
            owner2 = feature['properties']['OWN_NAME2']
            owner3 = feature['properties']['OWN_NAME3']
            owner_address_1 = feature['properties']['OWN_ADDR1']
            owner_address_2 = feature['properties']['OWN_ADDR2']
            owner_address_3 = feature['properties']['OWN_ADDR3']
            owner_address_4 = feature['properties']['OWN_ADDR4']
            owner_zip = feature['properties']['OWN_ZIP']
            number = feature['properties']['SITUS_ADDR']
            street_name = feature['properties']['SITUS_STRE']
            street_sfx = feature['properties']['SITUS_SUFF']
            city = feature['properties']['SITUS_COMM']
            zip = feature['properties']['SITUS_ZIP']
            legal_desc = feature['properties']['LEGLDESC']
            asr_land = feature['properties']['ASR_LAND']
            asr_impr = feature['properties']['ASR_IMPR']
            lot_area = feature['properties']['SHAPE_STAr']
            lot_length = feature['properties']['SHAPE_STLe']
            geometry = feature['geometry']
            model = models.SanDiego_Parcel(parcel_id=parcel_id, apn=apn, owner1=owner1, owner2=owner2, owner3=owner3,\
                                           owner_address_1=owner_address_1, owner_address_2=owner_address_2, owner_address_3=owner_address_3,\
                                           owner_address_4=owner_address_4, owner_zip=owner_zip, number=number, street_name=street_name,\
                                           street_sfx=street_sfx, city=city, zip=zip, lot_area=lot_area, lot_length=lot_length,\
                                           legal_desc=legal_desc, asr_land=asr_land, asr_impr=asr_impr, geometry=geometry)
            i += 1
            progress = '{0}/{1}'.format(str(i), str(num_lines))
            try:
                model.save()
                print('{0}: {1}'.format(progress, model))
            except:
                error_log.write(line.strip() + '\n')
                print('{0}: {1} -- Error found!'.format(progress, model))
    file.close()
    error_log.close()
    print('Done!')

#models.SanDiego_Zone.objects.all().delete()
