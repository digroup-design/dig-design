from django import forms

class ReportForm(forms.Form):
    address = forms.CharField(label='Address')