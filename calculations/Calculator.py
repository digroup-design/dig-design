import calculations.TxtConverter as TxtConverter
import simplejson as json
import database as db
import math

class ZoneReader:
    def __init__(self, zone_table:str, affordable_table:str):
        self.zone_table = zone_table
        self.affordable_table = affordable_table
        self.zone_table_fields = list(db.pg_get_fields(self.zone_table).keys())
        self.affordable_table_fields = list(db.pg_get_fields(self.affordable_table).keys())

    '''
    zone -- string representation of the zone
    lookup_model -- model class to look into
    returns the zone's object from the model database
    '''
    def get_zone(self, zone, name_col="name"):
        db.cur.execute("SELECT * FROM public.{0} WHERE {1}".format(
            self.zone_table, "LOWER({1})=LOWER('{0}')".format(zone, name_col)))
        result = db.cur.fetchone()
        if result:
            return dict(zip(self.zone_table_fields, result))
        else:
            return None

    #private function to use in get_rule_dicts.
    def _get_rule_dict(self, zone, lookup_col):
        zone_info = self.get_zone(zone)
        if lookup_col.lower().startswith("dev"): rule_dict_json = zone_info['development_regs']
        else: rule_dict_json = zone_info['use_regs']
        rule_dict = json.loads(rule_dict_json)

        if rule_dict['parent'] is None or str(rule_dict['parent']).lower() == 'none':
            return rule_dict['rule_dict']
        else: #if there is a parent, then we must get the parents' rule_dict too
            parent_rule_dict = self._get_rule_dict(rule_dict['parent'], lookup_col)
            parent_rule_dict.update(rule_dict['rule_dict'])
            return parent_rule_dict

    """
    Returns a nested dictionary containing both the use and development regulations of zone
    Inputs:
        zone - string name of zone to be looked up
        lookup_col - specify whether or return dict of 'use' or 'development' regulations
            If omitted, will return dict containing both dicts.
    """
    def get_rule_dicts(self, zone, lookup_col = None):
        #recursive function to get rule dict for one particular kind of zone
        if lookup_col is None:
            super_rule_dict = {
                'development': self._get_rule_dict(zone, "development"),
                'use': self._get_rule_dict(zone, "use")
            }
            return super_rule_dict
        else:
            if lookup_col.lower().startswith("dev"):
                return self._get_rule_dict(zone, "development")
            elif lookup_col.lower().startswith("use"):
                return self._get_rule_dict(zone, "use")
            else:
                print("Invalid lookup_col entered. Need 'development or 'use'.")
                return None
    """
    returns a dictionary containing all the affordable info for zones in the following format:
    { 'income level 0': { [min unit %] : {'density_bonus': [density bonus %], 'incentives': [# of incentives]} },
      'income level 1': ... } 
    """
    def get_affordable_dict(self):
        db.cur.execute("SELECT * FROM public.{0}".format(self.affordable_table))
        affordable = db.cur.fetchall()
        if len(affordable) > 0:
            affordable_dict = {}
            data_index = self.affordable_table_fields.index("data")
            label_index = self.affordable_table_fields.index("label")
            for a in affordable:
                data_json = str(a[data_index]).replace("'", '"')
                affordable_dict[str(a[label_index]).lower()] = json.loads(data_json)
            affordable_dict_formatted = {}
            for income, table_dict in affordable_dict.items():
                data_dict_formatted = {}
                for min_du, data_dict in table_dict.items():
                    data_dict_formatted[int(min_du)] = data_dict
                affordable_dict_formatted[income] = data_dict_formatted
            return affordable_dict_formatted
        else:
            return None

    """  
    returns an attribute in zone's rule_dict based on the input rule
        attr type must be 'category', 'rule', 'value' or 'footnotes'
        rule_class dictates if to be searched in Use Regulations, Development regulations or unspecified
        substr=True if rule can be a substring, else exact match required
    """
    def get_attr_by_rule(self, zone, rule, attr_type):
        attr_type = attr_type.lower()
        if attr_type in ['class', 'category', 'rule', 'value', 'footnotes']:
            rule_dict = self.get_rule_dicts(zone)
            for k, v in rule_dict.items():
                for v_sub in v.values():
                    if TxtConverter.match_search(v_sub['rule'], rule):
                        if attr_type == 'class':
                            return k
                        else:
                            return v_sub[attr_type]
        else:
            print("Invalid attribute - select from [class, category, rule, value, footnotes]")
            return None

    """
    returns a nested dictionary to be used by views.py
    """
    def get_rule_dict_output(self, zone):
        output_dict = {}
        rule_dicts = self.get_rule_dicts(zone)
        rule_dict_working = {}
        # clean out non-permitted use regs
        for k, v in rule_dicts.items():
            for k_sub, v_sub in v.items():
                if k.lower().startswith('use') and (v_sub['value'] in ['-', '--', '']):
                    pass
                else:
                    v_sub['class'] = (k + ' Regulations').title()
                    rule_dict_working[k_sub] = v_sub
        rule_dict = rule_dict_working
        for v in rule_dict.values():
            if v['category'] is None:
                v['category'] = ''
            if v['class'] not in output_dict.keys():
                output_dict[v['class']] = {}
            if v['category'] not in output_dict[v['class']].keys():
                output_dict[v['class']][v['category']] = {}

        for v in rule_dict.values():
            foot_text = ""
            if len(v['footnotes']) > 0:
                foot_text = " [" + ', '.join(v['footnotes']) + "]"
            output_dict[v['class']][v['category']][v['rule']] = \
                v['value'] + foot_text

        return output_dict

"""
Calculator is to be used as an abstract class for all Calculators. All methods are tested to work
for San Diego, but for other cities, should be overridden accordingly if their structure is different
"""
class Calculator:
    #the name of the Calculator is the city, and tells the program where all the data is found within the directory
    def __init__(self, name, zoneinfo_table, affordable_table):
        self.name = name
        self.affordable_dict = self.zone_reader.get_affordable_dict()
        self.zone_reader = ZoneReader(zoneinfo_table, affordable_table)

    def get_attr_by_rule(self, zoning_code, search_term):
        value = None
        unit = ''

        rule_name = self.zone_reader.get_attr_by_rule(zoning_code, search_term, 'rule')
        rule_value = self.zone_reader.get_attr_by_rule(zoning_code, search_term, 'value')
        if '(' in str(rule_name) and ')' in str(rule_name):
            unit = (rule_name.split('(')[-1])[0 : unit.find(')')]
        if rule_value is not None:
            try:
                value = float(rule_value.replace(',', ''))
            except: #TypeError?
                value = -1

        if value is None:
            return None
        else:
            return value, unit

    #calculates base max_dwelling units
    #generally designed to not need overriding if get_attr_by_rule works accordingly
    def get_max_dwelling_units(self, lot_size, zoning_code):
        max_density_tuple = self.get_attr_by_rule(zoning_code, 'max density')
        print(max_density_tuple)
        if max_density_tuple is None:
            print('No max density found')
            return -1

        density_unit = max_density_tuple[1].lower()
        density_value = max_density_tuple[0]

        if TxtConverter.match_search(density_unit, 'du/lot') or TxtConverter.match_search(density_unit, 'dwelling unit lot'):
            return density_value
        elif TxtConverter.match_search(density_unit, 'sf per') or TxtConverter.match_search(density_unit, 'sf/du') or\
                TxtConverter.match_search(density_unit, 'square feet per'):
            return lot_size/density_value
        else:
            print("Cannot determine units: {0}\nWill guess that it is SF/DU by default".format(density_unit))
            return lot_size/density_value

    """
    returns a dictionary of values regarding FAR and allowable dwelling area:
    { 'FAR-based rule' : ([FAR parameter], [calculated result]), 'FAR-based rule #2': ([FAR parameter 2], ...}
    """
    def get_dwelling_area_dict(self, zone, lot_area):
        try:
            dev_regs_dict = self.zone_reader.get_rule_dicts(zone, "development")
            floor_area_dict = {}
            for v in dev_regs_dict.values():
                if TxtConverter.match_search(v['rule'], "floor area ratio"):
                    far_value = float(v['value'])
                    far_calc = far_value * lot_area
                    floor_area_dict[v['rule']] = {'far_value': far_value,
                                                  'area': far_calc}
            return floor_area_dict
        except ValueError:
            return None

    """
    returns a dictionary of values regarding calculations for getting maximum affordable bonus densities
    {'very low income': (%affordable needed, %bonus density, #incentives, market-price units, affordable units, total units)...}
    """
    def get_max_affordable_bonus_dict(self, base_units, transit_priority = False):
        affordable_bonus_dict = {}
        for k, v in self.affordable_dict.items(): #v is a dictionary for each of the income levels
            affordable_percent = max(v.keys())
            if transit_priority:
                for k_sub, v_sub in v.items(): #find the minimum affordable_percent, given the maximum incentives
                    if (v_sub['incentives'] >= v[affordable_percent]['incentives']) and (k_sub < affordable_percent):
                        affordable_percent = k_sub
                bonus_density_percent = 100
            else:
                bonus_density_percent = float(v[affordable_percent]['density_bonus'])
            num_incentives = int(v[affordable_percent]['incentives'])
            affordable_units = int(math.ceil(base_units * affordable_percent/100))
            bonus_units = int(math.ceil(base_units * bonus_density_percent/100))
            total_units = base_units + bonus_units
            market_price_units = total_units - affordable_units
            affordable_bonus_dict[k.lower()] = {'percent_affordable': affordable_percent,
                                                'percent_bonus_density': bonus_density_percent,
                                                'incentives': num_incentives,
                                                'market_price_units': market_price_units,
                                                'affordable_units': affordable_units,
                                                'total_units': total_units}
        return affordable_bonus_dict