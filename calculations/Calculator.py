try:
    import calculations.CodeTree as CodeTree
    import calculations.TxtConverter as TxtConverter
    import calculations.GLOBALS as GLOBALS
except ModuleNotFoundError:
    import CodeTree
    import TxtConverter
    import GLOBALS
import math

#takes filename (txt) and adds its entries to tree's nodes
#each row represents a zoning code and each column the specific regulations
#transpose is True if the above is reversed
def txt_to_tree(file, tree, rule_class='', transpose=False):
    data_array = TxtConverter.txt_to_array(file, transpose, char_strip=['"'])
    rule_names = data_array[0]

    for r in range(1, len(data_array)):
        entry = data_array[r]
        node_name = entry[0]
        dictionary = TxtConverter.rules_to_dictionary(rule_names, entry, rule_class)
        tree.update_node(node_name, dictionary)
    return tree

#Calculator is to be used as an abstract class for all Calculators. All methods are tested to work
#for San Diego, but for other cities, should be overridden accordingly if their structure is different
class Calculator:
    #the name of the Calculator is the city, and tells the program where all the data is found within the directory
    def __init__(self, name):
        self.name = name
        self.tree = self._build_tree() #name of code, eg. RM-1-2, as string
        self._set_links(self.tree)
        self.code_tree = self.tree
        self.low_income = self._build_low_income()

    def _build_tree(self):
        #default implementation builds San Diego Tree
        file_dir = 'San Diego/zones/'
        tree = CodeTree.CodeTree(self.name)
        file_list = [f for f in GLOBALS.get_file_list(file_dir) if ('.txt' in f)]
        for filename in file_list:
            rule_class = ((filename.split("-")[0]).split("\\")[-1]).split(".")[0]
            rule_class = ((rule_class.split("-")[0]).split("/")[-1]).split(".")[0]
            file = GLOBALS.get_file(filename)
            txt_to_tree(file, tree, rule_class=rule_class, transpose=True)
        return tree

    # default implementation assumes hyphen in code names determine hierarchy
    def _set_links(self, tree):
        def get_parent_name(node_name):
            parent_split = node_name.split('-')
            if len(parent_split) > 1:
                parent_split.pop()
                return "-".join(parent_split)
            else:
                return tree.root_name

        # make sure all parent nodes already exist
        complete_check = False
        while not complete_check:
            key_array = []
            for k in tree.nodes:
                key_array.append(k)

            complete_check = True
            for k in key_array:
                complete_check = complete_check and tree.update_node(
                    get_parent_name(k))

        # e.g. RM-1 will have RM-1-X as children and RM as parent
        # in the end, all nodes without parents will directly link to root
        for k in tree.nodes:
            if k != tree.root_name:
                parent_name = get_parent_name(k)
                tree.set_parent(k, parent_name)

        for k in tree.nodes:
            parent = tree.nodes[k].parent
            if parent is None:
                print("{0} is the root node".format(k))
            else:
                print("{0} has parent {1}".format(k, parent.name))

    # builds the database for low-income calculations
    def _build_low_income(self):
        low_income_dict = {}
        try:
            file = GLOBALS.get_file("{0}/etc/Low Income.txt".format(self.name))
            info_array = TxtConverter.txt_to_array(file, char_strip=["\""])
            for i in range(1, len(info_array)): #skips the first row, header
                entry = info_array[i]
                print(entry)
                new_entry = { float(entry[1]) : entry[2:len(entry)] }
                if entry[0].lower() not in low_income_dict.keys():
                    low_income_dict[entry[0].lower()] = new_entry
                else:
                    low_income_dict[entry[0].lower()].update(new_entry)
                print(entry[0], new_entry)
        except FileNotFoundError:
            print("No low income data found.")
        return low_income_dict

    #searches the tree for a rule pertaining to search_term of a zoning_code
    #returns a tuple of (value, unit). Unit is '' if no unit (e.g. a ratio)
    def get_attr_by_rule(self, zoning_code, *search_terms):
        value = None
        unit = ''
        for s in search_terms:
            rule_name = self.tree.get_attr_by_rule(zoning_code, s, 'rule')
            rule_value = self.tree.get_attr_by_rule(zoning_code, s, 'value')
            try:
                unit = rule_name.split('(')[-1]
                unit = unit[0 : unit.find(')')]
            except:
                pass
            if rule_value is not None:
                try:
                    value = float(rule_value.replace(',', ''))
                except:
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
    def get_max_low_income_bonus(self, base_dwelling_units, household, min_base_units=0):
        if base_dwelling_units < min_base_units:
            return 0, 0, 0
        else:
            household = household.lower()
            if household not in self.low_income.keys():
                print("Invalid household type.")
                return None
            low_income_dict = self.low_income[household]
            max_percent = max(low_income_dict.keys())
            print(max_percent, low_income_dict[max_percent])
            aff_needed = math.ceil(base_dwelling_units * max_percent/100)
            du_bonus = math.ceil(float(low_income_dict[max_percent][0])/100 * base_dwelling_units)
            num_incentives = int(low_income_dict[max_percent][1])

            return aff_needed, du_bonus, num_incentives