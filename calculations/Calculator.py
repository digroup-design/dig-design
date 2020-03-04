from calculations.ZoneReader import ZoneReader
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

    def get_attr_by_rule(self, zoning_code, *search_terms):
        value = None
        unit = ''
        for s in search_terms:
            rule_name = self.zone_reader.get_attr_by_rule(zoning_code, s, 'rule')
            rule_value = self.zone_reader.get_attr_by_rule(zoning_code, s, 'value')
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
        max_density_tuple = self.get_attr_by_rule(zoning_code, 'max permitted density', 'maximum permitted density', 'residential density')
        print(max_density_tuple)
        if max_density_tuple is None:
            print('No max density found')
            return -1

        density_unit = max_density_tuple[1].lower()
        density_value = max_density_tuple[0]

        if density_unit in ['du/lot', 'dwelling units per lot', 'du per lot', 'dwelling units/lot']:
            return density_value
        elif density_unit in ['sf per du', 'sf/du', 'square feet per du']:
            return lot_size/density_value
        else:
            print("Cannot determine units: {0}".format(density_unit))
            return -1

    #calculates base max dwelling area
    #generally designed to not need overriding if get_attr_by_rule works accordingly
    def get_max_dwelling_area(self, lot_size, zoning_code, floors=1):
        far_tuple = self.get_attr_by_rule(zoning_code, 'floor area ratio', 'floor-area ratio')
        if far_tuple is None:
            print('No floor area ratio found')
            return -1
        return far_tuple * lot_size

    #returns a tuple (dwelling units needed, dwelling units bonus, number of incentives)
    def get_max_affordable_bonus(self, base_dwelling_units, household, min_base_units=0):
        if base_dwelling_units < min_base_units:
            return 0, 0, 0
        else:
            household = household.lower()
            if household not in self.affordable_dict.keys():
                print("Invalid household type.")
                return None
            low_income_dict = self.affordable_dict[household]
            max_percent = max(low_income_dict.keys())
            print(max_percent, low_income_dict[max_percent])
            aff_needed = math.ceil(base_dwelling_units * max_percent/100)
            du_bonus = math.ceil(float(low_income_dict[max_percent]['density_bonus'])/100 * base_dwelling_units)
            num_incentives = int(low_income_dict[max_percent]['incentives'])

            return aff_needed, du_bonus, num_incentives