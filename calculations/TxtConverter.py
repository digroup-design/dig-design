import numpy
import re
# This module handles all the conversions of txt to arrays that will be read by the CodeTree

"""
Converts a tab-delimited stream into a 2-d array 
inputs:
    text - an opened file to be translated into the tree
    transpose - if True, converts rows to columns and vice versa
    char_strip - list of characters to remove from array
"""
def txt_to_array(text, transpose=False, char_strip=[]):
    array = []
    for r in text:
        row_split = r.split('\t')
        entries = []
        for e in row_split:
            for c in char_strip:
                e = e.replace(c, "")
            entries.append(e.strip())
        array.append(entries)

    if transpose: return numpy.transpose(array)
    else: return array

"""
takes an entry_array and rules_array and outputs into a tuple:
    ((rule, category, rule_footnote), (value, value_footnote))
both inputs have to be more than length 1 and equal length
entry_array[0] must be the zone code, rules_array[0] is ignored ignored
rule class is the broad classification of rules - i.e. Development Regulations vs Use Regulations
"""
def rules_to_dictionary(rules_array, value_array, rule_class=''):
    dictionary = {}
    for i in range(1, len(value_array)):
        category = ''
        footnotes = []
        rule = rules_array[i]
        value = value_array[i]
        if '\\' in rule:  # searches for the category delimiter
            rule_parts = [r.strip() for r in rule.split('\\')]
            category = rule_parts[0]
            rule = rule_parts[1]

        if '[' in rule:  # searches for the footnote delimiter
            rule = rule.replace(']', '')
            rule_parts = [r.strip() for r in rule.split('[')]
            rule = rule_parts[0]
            footnotes.append(rule_parts[1])

        if '(' in value:  # searches for the footnote delimter
            value = value.replace(')', '')
            value_parts = value.split('(')
            value = value_parts.pop(0)
            footnotes = footnotes + value_parts  # add remaining parts to footnotes

        dictionary['\\'.join(filter(None, [rule_class, category, rule]))] = {
            'class': rule_class, 'rule': rule, 'category': category, 'value': value, 'footnotes': footnotes}
    return dictionary

# takes a string and replaces it with abbreviations, an array of tuples (full word, abbreviate)
def abbreviate(string, *abbreviations):
    string = string.lower()
    for a in abbreviations:
        string = string.replace(a[0].lower(), a[1].lower())
    return string

#returns true if search matches string
def match_search(string, search, in_order=True):
    search = re.sub(r'\W+', ' ', search).lower().strip()
    string = re.sub(r'\W+', ' ', string).lower().strip()
    if search == string: return True
    else:
        for s in search.split(' '):
            if s not in string:
                return False
            else:
                if in_order:
                    string = string.replace(s, '~').split('~')[-1]
        return True


