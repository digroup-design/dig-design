from calculations.ZoneReader import ZoneReader
import calculations.TxtConverter as TxtConverter
import math
import dig.models as models

"""
Calculator is to be used as an abstract class for all Calculators. All methods are tested to work
for San Diego, but for other cities, should be overridden accordingly if their structure is different
"""
class Calculator:
    #the name of the Calculator is the city, and tells the program where all the data is found within the directory
    def __init__(self, name):
        self.name = name
        self._build_zone_reader()
        self.affordable_dict = self.zone_reader.get_affordable_dict()

    def _build_zone_reader(self):
        self.zone_reader = ZoneReader(models.SanDiego_ZoneInfo, models.SanDiego_Affordable)

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
        dev_regs_dict = self.zone_reader.get_rule_dicts(zone, "development")
        floor_area_dict = {}
        for v in dev_regs_dict.values():
            if TxtConverter.match_search(v['rule'], "floor area ratio"):
                far_value = float(v['value'])
                far_calc = far_value * lot_area
                floor_area_dict[v['rule']] = {'far_value': far_value,
                                              'area': far_calc}
        return floor_area_dict

    """
    returns a dictionary of values regarding calculations for getting maximum affordable bonus densities
    {'very low income': (%affordable needed, %bonus density, #incentives, market-price units, affordable units, total units)...}
    """
    def get_max_affordable_bonus_dict(self, base_units):
        affordable_bonus_dict = {}
        for k, v in self.affordable_dict.items(): #v is a dictionary for each of the income levels
            affordable_percent = max(v.keys())
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