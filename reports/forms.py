from django import forms

city_list = ["San Diego", "San Jose"]
class ReportForm(forms.Form):
    address = forms.CharField(label='Address')
    city = forms.CharField(label='City')