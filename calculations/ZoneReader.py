from django.core.exceptions import ObjectDoesNotExist
import simplejson as json
import calculations.TxtConverter as TxtConverter

class ZoneReader:
    def __init__(self, zone_model, affordable_model):
        self.zone_model = zone_model
        self.affordable_model = affordable_model

    '''
    zone -- string representation of the zone
    lookup_model -- model class to look into
    returns the zone's object from the model database
    '''
    def get_zone(self, zone):
        try: return self.zone_model.objects.get(name__iexact=zone)
        except ObjectDoesNotExist: return None

    #private function to use in get_rule_dicts.
    def _get_rule_dict(self, zone, lookup_col):
        zone_info = self.get_zone(zone)
        if lookup_col.lower().startswith("dev"): rule_dict_json = zone_info.development_regs
        else: rule_dict_json = zone_info.use_regs
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
        affordable = self.affordable_model.objects.all()
        if len(affordable) > 0:
            affordable_dict = {}
            for a in affordable:
                data_json = str(a.data).replace("'", '"')
                affordable_dict[str(a.label).lower()] = json.loads(data_json)
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