#This module only exists to execute one-time scripts. Nothing here should be referenced in or executed any other modules.
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dig.settings')
django.setup() #This is needed to run models without manage.py

import simplejson as json
from django.core.exceptions import ObjectDoesNotExist
import dig.models as models
import calculations.TxtConverter as TxtConverter
import calculations.ZoneReader as ZoneReader

ENTRY_SUBSTRING = '"type": "Feature"'

def geojson_to_zone():
    file = open('data/San Diego/geojson/ZONING_BASE_SD.geojson')
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
#geojson_to_address()

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

def geojson_to_transit():
    file_dir = 'data/San Diego/geojson/TRANSIT_PRIORITY_AREA.geojson'
    num_lines = sum(1 for i in open(file_dir, 'rb'))
    i = 0
    error_log = open('Transit_log.txt', 'w')
    file = open(file_dir, 'r')
    for line in file:
        if ENTRY_SUBSTRING.lower() in line.lower():  # checks if line in geojson is a Feature entry
            feature = json.loads(line.strip().rstrip(','))
            name = feature['properties']['NAME']
            geometry = feature['geometry']
            model = models.SanDiego_TransitArea(name=name, geometry=geometry)
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
#geojson_to_transit()

#make sure there is no header
def export_affordable(model_class, *affordable_file):
    for a in affordable_file:
        label = a.split('.')[0]
        txt_array =TxtConverter.txt_to_array(open(a, 'r'), transpose=False, char_strip=["\""])
        entry_dict = {}
        for row in txt_array:
            entry_dict[int(row[0])] = {'density_bonus': float(row[1]), 'incentives': int(row[2])}
        data = json.dumps(entry_dict)
        model = model_class(label=label, data=data)
        model.save()

#export_affordable(models.SanDiego_Affordable, 'very low income.txt', 'low income.txt', 'moderate income.txt')

def export_zone(model_class, zone_file, footnotes_file=None):
    footnotes_dict = {}
    if footnotes_file:
        footnotes_array = TxtConverter.txt_to_array(open(footnotes_file, 'r'), transpose=False, char_strip=["\""])
        for f in footnotes_array:
            footnotes_dict[f[0]] = f[1]

    if 'dev' in zone_file.lower():
        rule_class = 'Development'
    elif 'use' in zone_file.lower():
        rule_class = 'Use'
    else:
        print('Invalid zone_file name')
        return None

    txt_array =TxtConverter.txt_to_array(open(zone_file, 'r'), transpose=True, char_strip=["\""])
    rules_row = txt_array[0]
    for i in range(1, len(txt_array)):
        name = txt_array[i][0]
        #the same logic is used for both dev and use regs
        zone_entry_dict = {'rule_dict': {}, 'footnotes_dict': {}} #omit parent
        for j in range(1, len(rules_row)):
            working_rule_dict= {
                'category': None,
                'rule': None,
                'value': None,
                'footnotes': []
            }
            if "\\" in rules_row[j]: #backslash in rule name in txt file denotes a category
                rules_parts = rules_row[j].split("\\")
                working_rule_dict['category'] = rules_parts[0]
                working_rule_dict['rule'] = rules_parts[1]
            else:
                working_rule_dict['rule'] = rules_row[j]
            if "[" in rules_row[j]: #rule-based footnotes are enclosed in [brackets]
                rule_parts = [r.strip() for r in working_rule_dict['rule'].replace(']', '').split('[')]
                working_rule_dict['rule'] = rule_parts.pop(0)
                working_rule_dict['footnotes'] += rule_parts
            curr_cell = txt_array[i][j]
            if "(" in curr_cell: #individual footnotes are enclosed in (parenthesis)
                value_parts = [c.strip() for c in curr_cell.replace(")", "").split("(")]
                working_rule_dict['value'] = value_parts.pop(0)
                working_rule_dict['footnotes'] += value_parts
                for k, v in footnotes_dict.items(): #only add relevant footnotes to save space
                    if k in working_rule_dict['footnotes']:
                        zone_entry_dict['footnotes_dict'][k] = v
            else:
                working_rule_dict['value'] = curr_cell
            entry_name = (rules_row[j].split('[')).pop(0).strip()
            zone_entry_dict['rule_dict'][entry_name] = working_rule_dict
        #if model already exists, get existing one. otherwise save
        try:
            zone_model = model_class.objects.get(name=name)
        except ObjectDoesNotExist:
            zone_model = model_class(name=name)
        if 'dev' in rule_class.lower(): #decide whether to update to dev or use regs in db
            working_dict = json.loads(zone_model.development_regs)
            working_dict.update(zone_entry_dict)
            zone_model.development_regs = json.dumps(working_dict)
        else:
            working_dict = json.loads(zone_model.use_regs)
            working_dict.update(zone_entry_dict)
            zone_model.use_regs = json.dumps(working_dict)
        zone_model.save()
    print("Done: {0}".format(zone_file))

#make sure column1 shows use parents; column2 shows dev parents
def set_parent(model_class, parent_file):
    parent_array = TxtConverter.txt_to_array(open(parent_file, 'r'), transpose=False, char_strip=["\""])
    for p in parent_array:
        try: zone_model = model_class.objects.get(name=p[0])
        except ObjectDoesNotExist: zone_model = model_class(name=p[0])

        if p[1].lower() == 'none': use_parent = None
        else: use_parent = p[1]

        use_regs_dict = json.loads(zone_model.use_regs)
        use_regs_dict['parent'] = use_parent
        zone_model.use_regs = json.dumps(use_regs_dict)

        if p[2].lower() == 'none': dev_parent = None
        else: dev_parent = p[2]

        dev_regs_dict = json.loads(zone_model.development_regs)
        dev_regs_dict['parent'] = dev_parent
        zone_model.development_regs = json.dumps(dev_regs_dict)

        zone_model.save()
        print("{0}'s parents are: {1} in use and {2} in dev".format(p[0], p[1], p[2]))

# file_list = [
#     ("dev regs RM.txt", "dev regs RM foot.txt")]

# file_list = [
#     ("use regs CC.tsv", 'use regs C footnotes.tsv'),
#     ("use regs Cb.tsv", 'use regs C footnotes.tsv'),
#     ("use regs C.tsv", 'use regs C footnotes.tsv'),
#     ("dev regs CN.tsv", 'dev regs CN footnotes.tsv'),
#     ("dev regs CC.tsv", 'dev regs CC footnotes.tsv'),
#     ("dev regs C.tsv", 'dev regs C footnotes.tsv')
# ]

file_list = [
    ('use regs I.tsv', 'use regs I foot.tsv'),
    ('dev regs I.tsv', 'dev regs I foot.tsv')
    ]

for p in ['C Parent.tsv', 'I Parent.tsv']:
    set_parent(models.SanDiego_ZoneInfo, p)

#for f in file_list: export_zone(models.SanDiego_ZoneInfo, f[0], f[1])

def test_code():
    string = 'Maximum permitted density (s.f.)'
    search = 'density max'
    print(TxtConverter.match_search(string, search, False))

#test_code()