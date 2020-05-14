from calculations.San_Diego.SanDiegoZoneQuery import SanDiegoZoneQuery
import math
from fractions import Fraction

class SanDiegoZoneR(SanDiegoZoneQuery):

    def get(self, zone:str, area:float=None, geometry:dict=None, transit_priority=False,
            stories:int=None, attached:bool=False, decimals:int=2) ->dict:
        if zone.upper().startswith("R"):
            return super().get(zone, area, geometry, transit_priority, stories, attached, decimals)
        else:
            raise ValueError("Zone must begin with 'R'")

    def _get_reference(self) ->str:
        return "https://docs.sandiego.gov/municode/MuniCodeChapter13/Ch13Art01Division04.pdf"

    def _get_dwelling_units(self) ->list:
        """Populates base_density, base_dwelling_units, max_dwelling_units"""
        du_unit = self.du_unit
        density_units = ("sf per DU", "DU per lot")
        density_info = self.data["density"]
        area = self.data["area"]
        if density_info[0]["unit"] == density_units[1]:
            return [self._makeentry(density_info[0]["value"], du_unit, None, None)]
        elif area is None:
            return None
        else:
            du_info = []
            density = density_info[0]["value"]
            note = density_info[0]["note"]
            num_units = area / density
            units_calc = "{0} sf / {1} sf per DU = {2} -> {3} DUs".format(
                round(area, self.decimals), density, num_units, math.ceil(num_units))
            du_info.append(self._makeentry(math.ceil(num_units), self.du_unit, note, units_calc))

            # check for affordable info
            base_units = du_info[0]["value"]
            affordable_dict = self._affordable(math.ceil(base_units), self.data["transit_priority"])
            if affordable_dict:
                max_units, market_units, affordable_units, num_incentives, annotation = 0, 1, 2, 3, 4
                for income, data in affordable_dict.items():
                    annot = data[annotation].split(";")
                    calc = annot[1].strip()
                    note = annot[0].strip() + (("; " + self.transit_note) if self.data["transit_priority"] else '')
                    du_info.append(self._makeentry(data[max_units], self.du_unit, note, calc))
            return sorted(du_info, key=lambda x: x["value"])

    def _get_far(self)->list:
        zone = self.data["zone"]
        area = self.data["area"]

        far_info = []  # far info should be stored in a tuple of (value, notes, calc)
        far_unit = None

        if self._re_match("^RS-1-[234567]$", zone) and area:
            far_note = "Sec 131.0446(a): Floor Area Ratio is based on the lot area in accordance with Table 131-04J."
            for row in self._get_table('131-04J', SanDiegoZoneQuery.tables):
                if area:
                    if float(row[0]) <= round(area) <= float(row[1]):
                        far_info.append(self._makeentry(row[2], far_unit, far_note, None))
                        break
                else:
                    far_calc = "{0} - {1} s.f.".format(str(row[0]), str(row[1]))
                    far_info.append(self._makeentry(row[2], far_unit, far_note, far_calc))
        elif self._re_match("RT-+.", zone):
            """
            Sec 131.0446(d): In the RT zones, up to 525 square feet of garage area may be excluded from the 
                calculation of gross floor area
            """
            for k, v in self.data['dev_regulations'].items():
                if self._re_match("floor.*area.*ratio", self._coalesce(v["subcategory"]).lower()):
                    # RT-zones have different FAR for 1-2 and 3 stories
                    far_info.append(self._makeentry(v['rule'], k, None))
        elif (self._re_match("RM-1-[23]", zone) or self._re_match("RM-2-[456]", zone) or
              self._re_match("RM-3-[789]", zone) or self._re_match("RM-4-1[01]", zone)):
            far_info += super()._get_far()
            if self._re_match("RM-1-[23]", zone) or self._re_match("RM-2-[456]", zone):
                far_note = "1/4 of FAR reserved for required parking. [See Sec 131.0446(e)]"
                req_parking = Fraction(1 / 4).limit_denominator(10)
            else:  # self._re_match("RM-3-[789]", zone) or self._re_match("RM-4-1[01]", zone
                far_note = "1/3 of buildable area reserved for required parking, unless developing Affordable Units"
                req_parking = Fraction(1 / 3).limit_denominator(10)
            far = far_info[0]["value"] * (1 - req_parking)
            far_calc = "{0} FAR x {1} required parking = {2} FAR".format(far_info[0]["value"], 1 - req_parking,
                                                                         far)
            far_info.append(self._makeentry(far, far_unit, far_note, far_calc))
        elif zone == "RM-5-12":
            far_note = "Sec 131.0446(d): Floor area ratio for buildings exceeding 4 stories or 48 feet of" \
                       " structure height shall be increased in accordance with Table 131-04K"
            far_calc_base = "Buildings at least {0} floors or {1} feet"
            # if either floor or height specified, find one row in table 131-04K that fits,
            # otherwise append entire table
            if self.data["floors"] or self.data["height"]:
                defaults = 1, 48, 1.80
                curr_far = self._makeentry(defaults[0], far_unit, far_note, None)
                for row in self._get_table("131-04K", SanDiegoZoneQuery.tables):
                    far_calc = far_calc_base.format(row[0], row[1])
                    if ((self._coalesce(self.data["floors"], defaults[0]) >= row[0] or
                         self._coalesce(self.data["height"], defaults[1]) >= row[1]) and
                            row[2] >= curr_far[0]):
                        curr_far = self._makeentry(row[2], far_unit, far_note, far_calc)
                far_info.append(curr_far)
            else:
                for row in self._get_table("131-04K", SanDiegoZoneQuery.tables):
                    far_calc = far_calc_base.format(row[0], row[1])
                    far_info.append(self._makeentry(row[2], far_unit, far_note, far_calc))
        else:
            far_info += super()._get_far()

        far_info.sort(key=lambda x: x["value"])
        return far_info

    def _get_buildable_area(self):
        area = self.data["area"]
        buildable_info = []
        build_unit = "sf"
        for far in self.data["far"]:
            far_val = far["value"]
            note = far["note"]
            buildable = far_val * area
            buildable_calc = "{0} FAR x {1} sf = {2} sf".format(far_val, round(area, self.decimals),
                                                                round(buildable, self.decimals))
            buildable_info.append(self._makeentry(round(buildable, self.decimals), build_unit, note, buildable_calc))
        return buildable_info