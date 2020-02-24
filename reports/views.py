from reports.forms import ReportForm
from django.shortcuts import render
from calculations.SanDiego import *
import math

# Create your views here.
def home(request):
    template = 'reports/home.html'

    address_proper = city_zip = None
    max_du = None
    max_density_calc = None
    zone_code = None
    apn = None
    transit_priority = False
    lot_size = None
    rule_dict = None
    units_mp_vl = units_aff_vl=incentives_vl=units_mp_l=\
        units_aff_l=incentives_l=units_mp_m=units_aff_m=incentives_m=\
        max_total_units = None

    if request.method == 'POST':
        form = ReportForm(request.POST)

        if form.is_valid():
            address = form['address'].value()

            address_proper = san_diego_gis.get_address_proper(address)
            print(address_proper)
            if address_proper is None:
                print("Address Not Found")
            else:
                city_zip = address_proper[1]
                address_proper = address_proper[0]
                parcel_feature = san_diego_gis.address_to_parcel_feature(address)
                apn = parcel_feature['properties']['APN']
                #Run the calculator here
                zone_code = san_diego_gis.get_zone('ZONING_BASE_SD', parcel_feature['geometry'])
                lot_size = parcel_feature['properties']['SHAPE_STAr']
                transit_priority = san_diego_gis.intersects_zone('TRANSIT_PRIORITY_AREA', parcel_feature['geometry'])

                if zone_code in san_diego.tree.nodes.keys():
                    max_density = san_diego.get_attr_by_rule(zone_code, 'max permitted density', 'maximum permitted density')
                    max_du = san_diego.get_max_dwelling_units(lot_size, zone_code)
                    max_density_calc = "{0} SF/{1} SF = {2} or ".format(str(round(lot_size, 2)), str(max_density[0]), max_du)
                    max_du = int(math.ceil(max_du))
                    rule_dict = san_diego.tree.get_rule_dict_output(zone_code)

                    if max_du >= 5: #todo: don't hard-code this minimum
                    # returns min affordable, bonus du, incentives
                        vl = san_diego.get_max_low_income_bonus(max_du, "Very Low Income")
                        l = san_diego.get_max_low_income_bonus(max_du, "Low Income")
                        m = san_diego.get_max_low_income_bonus(max_du, "Moderate Income")
                        incentives_vl = vl[2]
                        incentives_l = l[2]
                        incentives_m = m[2]
                        units_aff_vl = vl[0]
                        units_aff_l = l[0]
                        units_aff_m = m[0]
                        units_mp_vl = max_du + vl[1] - units_aff_vl
                        units_mp_l = max_du + l[1] - units_aff_l
                        units_mp_m = max_du + m[1] - units_aff_m
                        max_total_units = max([max_du + vl[1], max_du + l[1], max_du + m[1]])
    else:
        form = ReportForm()

    output = {
        'form': form,
        'address_proper' : address_proper,
        'city_zip' : city_zip,
        'zone' : zone_code,
        'area' : lot_size,
        'apn' : apn,
        'transit_priority' : transit_priority,
        'max_du_calc': max_density_calc,
        'max_du': max_du,
        'rule_dict': rule_dict,
        'units_mp_vl': units_mp_vl,
        'units_aff_vl': units_aff_vl,
        'incentives_vl': incentives_vl,
        'units_mp_l': units_mp_l,
        'units_aff_l': units_aff_l,
        'incentives_l': incentives_l,
        'units_mp_m': units_mp_m,
        'units_aff_m': units_aff_m,
        'incentives_m': incentives_m,
        'max_total_units': max_total_units
    }

    return render(request, template, output)

def about(request):
    return render(request, 'reports/about.html')