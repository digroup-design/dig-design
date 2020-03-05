from reports.forms import ReportForm
from django.shortcuts import render
import calculations.SanDiego as SanDiego
import math

san_diego_calc = SanDiego.CalculatorSanDiego("San Diego")
san_diego_gis = SanDiego.GISSanDiego("San Diego")

def home(request):
    template = 'reports/home.html'

    address_proper_street = address_proper_city = None
    base_du = None
    max_du = None
    max_density_calc = None
    zone_code = None
    apn = None
    transit_priority = False
    lot_size = None
    rule_dict = None
    dwelling_area_dict = None
    affordable_dict = None

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

                    dwelling_area_dict = san_diego_calc.get_dwelling_area_dict(zone_code, lot_size)
                    print(dwelling_area_dict)
                    if zone_data is not None:
                        max_density = san_diego_calc.get_attr_by_rule(zone_code, 'max density')
                        print("Max density: {0}".format(max_density))
                        base_du = san_diego_calc.get_max_dwelling_units(lot_size, zone_code)
                        max_density_calc = "{0} / {1} = {2} or ".format(str(round(lot_size, 2)), str(max_density[0]), base_du)
                        base_du = int(math.ceil(base_du))
                        rule_dict = san_diego_calc.zone_reader.get_rule_dict_output(zone_code)

                        if base_du >= 5: #todo: don't hard-code this minimum
                            affordable_dict = san_diego_calc.get_max_affordable_bonus_dict(base_du)
                            print(affordable_dict)
                            total_dus = []
                            for v in affordable_dict.values():
                                total_dus.append(v['total_units'])
                            max_du = max(total_dus)
                        else:
                            max_du = base_du
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
        'base_du_calc': max_density_calc,
        'base_du': base_du,
        'rule_dict': rule_dict,
        'dwelling_area_dict': dwelling_area_dict,
        'affordable_dict': affordable_dict,
        'max_du': max_du
    }

    return render(request, template, output)

def about(request):
    return render(request, 'reports/about.html')