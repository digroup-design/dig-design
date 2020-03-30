from reports.forms import ReportForm
from django.shortcuts import render
import calculations.SanDiego as SanDiego
import calculations.SanJose as SanJose

#TODO: Account for different ways to input suffixes
ADDRESS_ABREVS = {'street': 'st',
                  'avenue': 'ave',
                  'av': 'ave',
                  'boulevard': 'blvd',
                  'terrace': 'ter',
                  'terr': 'ter',
                  }

def home(request):
    template = 'reports/home.html'

    output = {}

    if request.method == 'POST':
        form = ReportForm(request.POST)

        if form.is_valid():
            output = {"has_info": False}
            address = form['address'].value()
            city = form['city'].value().lower().strip()

            if city.lower().strip() == "san diego":
                address_query = SanDiego.SanDiego()
                output["has_info"] = True
                output.update(address_query.get(address))
            else:
                output = {"has_info": False, "error": "Invalid City"}

    else:
        form = ReportForm()

    output["form"] = form
    return render(request, template, output)

def about(request):
    return render(request, 'reports/about.html')