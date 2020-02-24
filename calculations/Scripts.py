#This module only exists to execute one-time scripts. Nothing here should be referenced in or executed any other modules.
import simplejson as json
import os
import GLOBALS

ENTRY_SUBSTRING = '"type": "Feature"'

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

def build_address_book(folder, filename):
    filedir = _get_geojson_dir(folder, filename)
    file = open(filedir, 'r')

    address_book = open('addresses.txt', 'w')
    for line in file:
        if ENTRY_SUBSTRING.lower() in line.lower():
            feature = json.loads(line.strip().rstrip(','))
            properties = feature['properties']
            address_num = str(int(properties['ADDRNMBR']))
            street = properties['ADDRNAME']
            suffix = properties['ADDRSFX']

            if street is not None:
                street = street.title()
            if suffix is not None:
                suffix = suffix.title()

            address_full = ' '.join(filter(None, [address_num, street, suffix]))
            print(address_full)
            address_book.write(address_full+'\n')

    for f in file, address_book:
        f.close()

#build_address_book('San Diego', 'Address_APN.geojson')

import sqlite3
print(sqlite3.sqlite_version)
