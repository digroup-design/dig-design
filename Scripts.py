"""
This module only exists to execute one-time scripts.
Nothing here should be referenced in or executed any other modules.
"""
import simplejson as json
from django.core.exceptions import ObjectDoesNotExist
import calculations.TxtConverter as TxtConverter
import calculations.AddressQueryFactory as AddressQueryFactory
from calculations.AddressQueryFactory import AddressQueryFactory as Q
import database as db
from time import time

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
    ('use regs rmx.tsv', 'use regs rmx foot.tsv'),
    ('dev regs rmx.tsv', 'dev regs rmx foot.tsv')
    ]


# import calculations.InputValidate as V
# start = time()
# res = V.autofill_list("2405 union", "sandiego_addresses", "full_addr", "apn")
# end = time()
# print(res)
# print(end - start)

# q = Q()
# print(q.get("san jose", "ca", '620 n 2nd st'))
# print(q)
#
# santa_clara_tests = ('23029119', '23024008', '23029096')
# for s in santa_clara_tests:
#     print(q.get("santa clara", "ca", apn=s)['opportunity_zone'])
#     print(q)
#
# print(q.get("san diego", "ca", "1401 national city blvd")['opportunity_zone'])
# print(q)

# from calculations.SanDiego import SanDiego
# sd = SanDiego()
# cur = sd.cur
# query = """
#     SELECT p.apn, oz.namelsad, a.full_addr
#     FROM public.sandiego_parcels p, public.ca_opportunity_zones oz, public.sandiego_addresses a
#     WHERE
#         a.full_addr = '1401 NATIONAL CITY BLVD' AND
#         ST_Intersects(
#             ST_Transform(ST_GeomFromText(ST_AsText(ST_GeomFromGeoJSON({0})), {1}), {2}),
#             ST_GeomFromText(ST_AsText(ST_GeomFromGeoJSON(oz.geometry), 4269))
#         )
#     LIMIT 5;
#     """.format("p.geometry", str(4326), str(4269))
# cur.execute(query)
# print(cur)



print(csv_to_dict("sandiego_test_data.csv", ';'))

# data = sd.get(address="2405 union st")
# geo = data['geometry']
# print(geo)
# g = sd.st_transform(geo, 4326, 3857)
# print(g)

