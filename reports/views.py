from reports.forms import ReportForm
from django.shortcuts import render
import calculations.SanDiego as SanDiego
import math

san_diego_calc = SanDiego.CalculatorSanDiego("San Diego")
san_diego_gis = SanDiego.GISSanDiego("San Diego")

def home(request):
    template = 'reports/home.html'

    address_proper_street = address_proper_city = None
    max_du = None
    max_density_calc = None
    zone_code = None
    apn = None
    transit_priority = False
    lot_size = None
    rule_dict = None
    units_mp_vl = units_aff_vl = incentives_vl = units_mp_l =\
        units_aff_l = incentives_l = units_mp_m = units_aff_m = incentives_m =\
        max_total_units = None

    if request.method == 'POST':
        form = ReportForm(request.POST)

        if form.is_valid():
            address = form['address'].value()

            address_feature = san_diego_gis.get_address_feature(address)

            if address_feature is None:
                print("Address Not Found")
            else:
                address_proper = san_diego_gis.get_address_proper(address_feature)
                print('\n'.join(address_proper))
                address_proper_street = address_proper[0]
                address_proper_city = address_proper[1]
                apn = address_feature.apn

                #Run the calculator here
                parcel_feature = san_diego_gis.get_parcel_feature(address_feature.parcel_id)
                if parcel_feature is None:
                    pass
                else:
                    zone_code = san_diego_gis.get_zone(parcel_feature)
                    print(zone_code)
                    lot_size = float(parcel_feature.lot_area)
                    transit_priority = san_diego_gis.is_transit_area(parcel_feature)

                    zone_data = san_diego_calc.zone_reader.get_zone(zone_code)
                    if zone_data is not None:
                        max_density = san_diego_calc.get_attr_by_rule(zone_code, 'max density')
                        print("Max density: {0}".format(max_density))
                        max_du = san_diego_calc.get_max_dwelling_units(lot_size, zone_code)
                        max_density_calc = "{0} SF/{1} SF = {2} or ".format(str(round(lot_size, 2)), str(max_density[0]), max_du)
                        max_du = int(math.ceil(max_du))
                        rule_dict = san_diego_calc.zone_reader.get_rule_dict_output(zone_code)

                        if max_du >= 5: #todo: don't hard-code this minimum
                        # returns min affordable, bonus du, incentives
                            vl = san_diego_calc.get_max_affordable_bonus(max_du, "Very Low Income")
                            l = san_diego_calc.get_max_affordable_bonus(max_du, "Low Income")
                            m = san_diego_calc.get_max_affordable_bonus(max_du, "Moderate Income")
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
        'address_proper': address_proper_street,
        'city_zip': address_proper_city,
        'zone': zone_code,
        'area': lot_size,
        'apn': apn,
        'transit_priority': transit_priority,
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