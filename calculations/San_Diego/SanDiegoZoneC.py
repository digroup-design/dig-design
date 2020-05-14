from calculations.San_Diego.SanDiegoZoneQuery import SanDiegoZoneQuery
import math

class SanDiegoZoneC(SanDiegoZoneQuery):
    def _get_reference(self) ->str:
        return "https://docs.sandiego.gov/municode/MuniCodeChapter13/Ch13Art01Division05.pdf"

    def _get_density(self)->list:
        zone = self.data["zone"]
        density_info = []
        if zone in ("CO-2-1", "CO-2-2", "CP-1-1"):
            note = "Residential use not permitted."
            density_info.append(self._makeentry(value=None, unit=None, note=note, calc=None))
        else:
            density_info += super()._get_density()
        return density_info

    def _get_dwelling_units(self)->list:
        area = self.data["area"]
        if area is None or self.data["zone"] in ("CO-2-1", "CO-2-2", "CP-1-1"):
            return None

        du_info = []
        du_unit = "dwelling units"
        density = self.data["density"][0]["value"]
        note = "Base max dwelling units"
        base_du = area / density
        calc = "{0} sf / {1} sf per DU = {2} -> {3} DU".format(area, density, round(base_du, self.decimals),
                                                               math.ceil(base_du))
        du_info.append(self._makeentry(value=math.ceil(base_du), unit=du_unit, note=note, calc=calc))

        # do affordable calculations
        affordable = self._affordable(math.ceil(base_du), self.data["transit_priority"])
        if affordable:
            max_units, market_units, affordable_units, num_incentives, annotation = 0, 1, 2, 3, 4
            for income, data in affordable.items():
                annot = data[annotation].split(";")
                calc = annot[1].strip()
                note = annot[0].strip() + (("; " + self.transit_note) if self.data["transit_priority"] else '')
                du_info.append(self._makeentry(value=data[max_units], unit=du_unit, note=note, calc=calc))
        return sorted(du_info, key=lambda x: x["value"])

    def _get_far(self):
        #TODO: Child Care
        far_info = []
        for k, v in self.data['dev_regulations'].items():
            if self._re_match(".*floor.*area.*ratio.*", k.lower()):
                if self._isnumber(v['rule']):
                    far_note = "Max Floor Area Ratio (Base)" if len(far_info) == 0 else k
                    far_info.append(self._makeentry(value=v['rule'], unit=None, note=far_note, calc=None))
                    if self._re_match(".*bonus.*", k.lower()):
                        base_far = far_info[0]["value"]
                        far_info.append(self._makeentry(
                            value=v['rule'] + base_far,
                            unit=None,
                            note="Base FAR + " + k,
                            calc="{0} + {1} = {2}".format(v['rule'], base_far, v['rule'] + base_far)
                        ))
        return sorted(far_info, key=lambda x: x["value"])

    def _get_buildable_area(self):
        area = self.data["area"]
        if area is None:
            return None

        decimals = self.decimals
        buildable_info = []
        build_unit = "sf"
        for f in self.data["far"]:
            build_area = f["value"] * area
            build_note = f["note"]
            build_calc = "{0} sf x {1} FAR = {2}".format(round(area, decimals),
                                                         f["value"], round(build_area, decimals))
            buildable_info.append(self._makeentry(value=round(build_area, decimals),
                                                  unit=build_unit, note=build_note, calc=build_calc))
        return sorted(buildable_info, key=lambda x: x["value"])