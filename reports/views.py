from reports.forms import ReportForm
from django.shortcuts import render
import calculations.SanDiego as SanDiego
from django.http import JsonResponse

#TODO: Account for different ways to input suffixes
ADDRESS_ABREVS = {'street': 'st',
                  'avenue': 'ave',
                  'av': 'ave',
                  'boulevard': 'blvd',
                  'terrace': 'ter',
                  'terr': 'ter',
                  }

def send_json(request, address=None, apn=None, city="san_diego", state="ca"):
    data = {}
    address_query = None

    if state.lower() in ["ca", "california"]:
        if city.lower() in ["san_diego", "san diego"]:
            address_query = SanDiego.SanDiego()

    if address_query:
        if address: data = address_query.get(street_address=address.replace("_", " "))
        elif apn: data = address_query.get(apn=apn)

    return JsonResponse(data)


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