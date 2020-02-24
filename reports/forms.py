from django import forms
from calculations.SanDiego import *

zone_list =  san_diego.tree.key_choices()
class ReportForm(forms.Form):
    address = forms.CharField(label='Address')