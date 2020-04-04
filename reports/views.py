from reports.forms import ReportForm
from django.shortcuts import render
from django.http import JsonResponse
import simplejson as json

import calculations.SanDiego as SanDiego
import calculations.SanJose as SanJose
import calculations.SantaClara_County as SantaClara_County

#TODO: Account for different ways to input suffixes
ADDRESS_ABREVS = {'street': 'st',
                  'avenue': 'ave',
                  'av': 'ave',
                  'boulevard': 'blvd',
                  'terrace': 'ter',
                  'terr': 'ter',
                  }

def send_json(request, address=None, apn=None, city="san diego", state="ca"):
    #TODO: url fields should allow spaces, but do not due to URL restrictions.
    # Should figure out work-around using %20 or regex

    if address: address = address.replace("_", " ")
    if apn: apn = apn.replace("_", " ")
    city = city.replace("_", " ")
    state = state.replace("_", " ")

    data = {}
    address_query = None

    if state.lower() in ["ca", "california"]:
        if city.lower() in SanDiego.city_list:
            address_query = SanDiego.SanDiego()
        elif city.lower() == "san jose":
            address_query = SanJose.SanJose()
        elif city.upper() in SantaClara_County.city_list:
            address_query = SantaClara_County.SantaClara_County()

    if address_query:
        if address: data = address_query.get(address=address)
        elif apn: data = address_query.get(apn=apn)

    return JsonResponse(data)


def home(request):
    template = 'reports/home.html'

    output = {"has_info": False}

    if request.method == 'POST':
        form = ReportForm(request.POST)

        if form.is_valid():
            address = form['address'].value().lower().strip().replace(" ", "_")
            city = form['city'].value().lower().strip().replace(" ", "_")

            json_data = json.loads(send_json(request, address=address, city=city, state="ca").content)
            if json_data == {}:
                output["error"] = "Invalid City"
            else:
                output["has_info"] = True
                output.update(json_data)
                print(output)

    else:
        form = ReportForm()

    output["form"] = form
    return render(request, template, output)

def about(request):
    return render(request, 'reports/about.html')