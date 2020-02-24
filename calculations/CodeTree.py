try:
    import calculations.TxtConverter as TxtConverter
except ModuleNotFoundError:
    import TxtConverter

# Notes:
# When instantiated and called outside the terminal, nodes should only have to be referred to by their names "e.g. RM-1-1"
# Also, all calls should be done in the context of CodeTree. CodeNode is technically all "private"

#Generally, all functions used by any City's code reader should be in this module
def txt_to_array(txt_file, transpose = False):
    return TxtConverter.txt_to_array(txt_file, transpose=transpose, char_strip=["\""])

# CodeNode are the nodes that represent each Zoning Code that create CodeTree.
class _CodeNode:
    def __init__(self, name, parent=None, rule_dict=None):
        self.name = name #name of code, eg. RM-1-2, as string
        self.parent = parent
        self.children = []
        if rule_dict is None:
            self.rule_dict = {}
        else:
            self.rule_dict = rule_dict

    #recursively retrieves full dictionary of rules, all the way to parent node
    #if child and parent has same rule, child's will override
    def get_rule_dict(self):
        if self.parent is None:
            return self.rule_dict.copy()
        else:
            working_dict = self.parent.get_rule_dict() #copy the parent dictionary
            working_dict.update(self.rule_dict) #update/combine the copy with current rule dict
            return working_dict

    #reads a dictionary of new rules and adds it
    def update_rules(self, rule_dict):
        self.rule_dict.update(rule_dict)

    #add a child to the node
    def add_child(self, child_node):
        self.children.append(child_node)
        child_node.parent = self

    def set_parent(self, parent_node):
        parent_node.add_child(self)

class CodeTree:
    #every node in CodeTree must have a unique name
    #nodes in trees are stored in a dictionary -- node.name : node
    def __init__(self, root_name):
        self.root_name = root_name
        self.root = _CodeNode(root_name) #the tree automatically creates a root based on its name
        self.nodes = {root_name : self.root}

    #updates the node's current dictionary with dictionary
    #this effectively adds new rules. if there is overlap, new rules override the old ones
    #returns True if node already exists; returns False if new node had to be made
    def update_node(self, node_name, dictionary={}):
        if node_name not in self.nodes.keys(): #if the node does not exist, it will be created
            self.nodes[node_name] = _CodeNode(node_name, rule_dict = dictionary)
            return False
        else:
            self.nodes[node_name].update_rules(dictionary)
            return True

    #returns a tuple of paired tuples to be used in django's choiceFields
    def key_choices(self):
        keys_list = []
        #i = 1
        for k, v in self.nodes.items():
            if len(v.children) == 0:
                keys_list.append((k, k))
                #i += 1
        return tuple(keys_list)

    #sets the parent of the node to a parent, based on the nodes' names
    def set_parent(self, node_name, parent_name):
        if parent_name not in self.nodes:
            self.update_node(parent_name, {})
        self.nodes[node_name].set_parent(self.nodes[parent_name])
        self.nodes[parent_name].add_child(self.nodes[node_name])

    #returns the node within tree that has the given name
    def get_node(self, node_name):
        try:
            return self.nodes[node_name]
        except KeyError:
            print('{0} not found'.format(node_name))
            return _CodeNode("NULL")

    #returns entire dictionary of rules that pertain to this zoning code
    def get_rule_dict(self, node_name):
        return self.get_node(node_name).get_rule_dict()

    #converts rule_dict into a nested dictionary to be read for output purposes
    #use_regs_text is used to identify class of items that should be cleaned
        #i.e. remove all the non-permitted uses
    def get_rule_dict_output(self, node_name, use_regs_text="Use Regulations"):
        output_dict = {}
        rule_dict = self.get_rule_dict(node_name)
        rule_dict_working = {}
        #clean out non-permitted use regs
        for k, v in rule_dict.items():
            if v['class'] == use_regs_text and (v['value'] in ['-', '--', '']):
                pass
            else:
                rule_dict_working[k] = v
        rule_dict = rule_dict_working

        for v in rule_dict.values():
            if v['class'] not in output_dict.keys():
                output_dict[v['class']] = {}
            if v['category'] not in output_dict[v['class']].keys():
                output_dict[v['class']][v['category']] = {}

        for v in rule_dict.values():
            foot_text = ""
            if len(v['footnotes']) > 0:
                foot_text = " [" + ', '.join(v['footnotes']) + "]"
            output_dict[v['class']][v['category']][v['rule']] = \
                v['value'] +  foot_text

        return output_dict


    def rule_to_value(self, node_name, rule, substr=True):
        return self.get_attr_by_rule(node_name, rule, 'value', substr)

    def get_attr_by_rule(self, node_name, rule, attr, substr=True):
        if attr in ['class', 'category', 'rule', 'value', 'footnotes']:
            rule_dict = self.get_rule_dict(node_name)
            for v in rule_dict.values():
                if (substr and TxtConverter.is_substring(v['rule'], rule)) or \
                        ((not substr) and v['rule']) == rule:
                    return v[attr]
        else:
            print("Invalid attribute - select from [class, category, rule, value, footnotes]")
            return None

    def delete_node(self, node_name, cascade=True):
        #TODO: recursive way to delete nodes' children too
        del self.nodes[node_name]