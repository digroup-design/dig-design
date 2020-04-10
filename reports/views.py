from reports.forms import ReportForm
from django.shortcuts import render
from django.http import JsonResponse
import simplejson as json
from calculations.AddressQueryFactory import AddressQueryFactory

def send_json(request, address=None, apn=None, city="san diego", state="ca"):
    #TODO: url fields should allow spaces, but do not due to URL restrictions.
    #   Should figure out work-around using %20 or regex
    if address: address = address.replace("_", " ")
    elif apn: apn = apn.replace("_", " ")
    city = city.replace("_", " ")
    state = state.replace("_", " ")

    q = AddressQueryFactory()
    data = q.get(city, state, address=address, apn=apn)
    print(q)
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

    else:
        form = ReportForm()

    output["form"] = form
    return render(request, template, output)

def about(request):
    return render(request, 'reports/about.html')