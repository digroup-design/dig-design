from fractions import Fraction
from calculations.ZoneQuery import ZoneQuery, area
import math

class SanDiegoZoneQuery(ZoneQuery):
    """
    Data from: https://www.sandiego.gov/city-clerk/officialdocs/municipal-code/chapter-13
    """
    MIN_AFFORDABLE = 5
    use_regs = "sandiego_regulations_use"
    dev_regs = "sandiego_regulations_dev"
    tables = "sandiego_regulations_tables"

    def get(self, zone:str, attr:dict=None):
        """
        :param zone: the string name of the zone to match with what's in the database
        :param attr: a dict of attributes that may be relevant to zoning calculations. The allowable keys for attr are:
            geometry: dict representation of the parcel/address's geojson. This is usually optional, but useful for
                zones that reference other geographical locations.
            floors - number of floors in a dwelling unit
            transit_priority - True/False, used for affordable calculations
            attached - True/False (False for detached)
        :return: self.data, populated with relevant information. These include:
            zone
            desc
            reference
            use_regulations
            dev_regulations
            base_far
            max_far
            base_density: tuple(density, unit)
            base_buildable_area
            max_buildable_area
            base_dwelling_units
            max_dwelling_units
        """
        self.attr = {
            "geometry": None,
            "area": None,
            "transit_priority": None,
            "floors": None,
            "height": None,
            "attached": None,
            "decimals": None #of decimals to round results to
        }
        if attr: self.attr.update(attr)

        self.data["zone"] = zone = zone.upper().replace("CUPD-", '')
        if self.attr["area"] is None and self.attr["geometry"] is not None:
            self.attr["area"] = area(self.attr["geometry"])

        if "-" in self.data["zone"]:
            zone_cat = self.data["zone"].split("-")[0]
        else:
            zone_cat = self.data["zone"]

        def _set_reg_dict(zone_key):
            if zone.startswith("CT-"):
                """Ch15, Art5, Div2 - Sec 155.0236"""
                ct_table = (
                    ("CT-5-4", "CC-5-4", "CC-5-4", "RM-2-5", True),
                    ("CT-2-3", "CU-2-3", "CU-2-3", "RM-2-5", True),
                    ("CT-2-4", "CU-2-4", "CU-2-4", "RM-2-5", True),
                    ("CT-3-3", "CP-1-1", "CU-3-3", "RM-1-2", False)
                )
                for r in ct_table:
                    """Development in r[0] is subject to the r[1] zone regulations if any portion of development is 
                    also within a r[2] zone {{if r[4], and fronts a major street designated in community plan}},
                    otherwise r[3] zone regulations apply."""
                    if zone_key == r[0]:
                        cond = True #TODO: write logic for conditions, using r[2] and r[4]
                        zone_key = r[1] if cond else r[3]
                    #TODO: logic for Table 155-02A

            self.data["dev_regulations"] = self._find_regs(zone_key, SanDiegoZoneQuery.dev_regs)
            self.data["use_regulations"] = self._find_regs(zone_key, SanDiegoZoneQuery.use_regs)
            if None in (self.data["dev_regulations"], self.data["use_regulations"]):
                raise ValueError("Data for {0} not found.".format(zone))

        _set_reg_dict(zone)

        if zone_cat.startswith("R"):
            self._zone_r(zone, self.attr)
        elif zone_cat.startswith("CCPD"):
            self._zone_ccpd(zone, self.attr)
        elif zone_cat.startswith("CU") or zone_cat.startswith("CT"):
            self._zone_cupd(zone, self.attr)
        elif zone_cat.startswith("C"):
            self._zone_c(zone, self.attr)
        elif zone_cat.startswith("I"):
            self._zone_i(zone, self.attr)
        elif zone_cat.startswith("O"):
            self._zone_o(zone, self.attr)
        elif zone_cat.endswith("MX"):
            self._zone_mx(zone, self.attr)
        return self.data

    def _default_far(self)->dict:
        """default implementation of finding FAR if no special cases"""
        for k, v in self.data['dev_regulations'].items():
            if self._re_match(".*floor.*area.*ratio.*", k.lower()):
                return self._makeentry(value=v['rule'], unit=None, note=k, calc=None)

    def _default_density(self)->dict:
        """default implementation of finding permitted density if no special cases"""
        for k, v in self.data['dev_regulations'].items():
            if self._re_match("max.* density", k.lower()):
                if self._re_match(".*(.*du .* lot.*).*", k.lower()):
                    density_unit = "DU per lot"
                else:
                    density_unit = "sf per DU"
                return self._makeentry(value=v['rule'], unit=density_unit, note=k, calc=None)

    def _default_dwelling_units(self, area:float, density_info:list, do_affordable=True, transit_priority=False)->list:
        """
        default implementation of finding possible numbers of dwelling units
        :param area: lot area of parcel
        :param density_info: list of dict entries holding density-related data
        :param do_affordable: True if affordable calculations apply
        :param transit_priority: True if parcel lies within a transit priority area
        :return: list of dwelling units calculations in ascending order
        """
        du_info = []
        du_unit = "dwelling units"
        area_unit = "sf"
        dec_round = 2
        for d in density_info:
            try:
                dwelling_units = area / d["value"]
                note = d["note"]
                calc = "{0} {1} / {2} {3} = {4} -> {5} {6}".format(
                    round(area, dec_round), area_unit,
                    d["value"], d["unit"],
                    round(dwelling_units, dec_round), math.ceil(dwelling_units), du_unit
                )
            except TypeError:
                dwelling_units = None
                note = "Invalid density value"
                calc = None
            du_info.append(self._makeentry(value=math.ceil(dwelling_units), unit=du_unit, note=note, calc=calc))

        if do_affordable and len(du_info)> 0:
            transit_note = "100% density bonus requires avg. unit size of 600 SF & max. unit size of 800 SF"
            base_units = du_info[0]["value"]
            affordable_dict = self._affordable(math.ceil(base_units), transit_priority)
            if affordable_dict:
                max_units, market_units, affordable_units, num_incentives, annotation = 0, 1, 2, 3, 4
                for income, data in affordable_dict.items():
                    annot = data[annotation].split(";")
                    calc = annot[1].strip()
                    note = annot[0].strip() + (("; " + transit_note) if transit_priority else '')
                    du_info.append(self._makeentry(data[max_units], du_unit, note, calc))

        return sorted(du_info, key=lambda x: x["value"])

    def _default_buildable_area(self, area:float, far_info:list)->list:
        buildable_info = []
        far_unit = None
        dec_round = 2
        for b in far_info:
            buildable_area = area * b["value"]
            note = b["note"]
            calc = "{0} {1} x {2} (FAR) = {3} {1}".format(
                round(area, dec_round), b["unit"],
                b["value"], round(buildable_area, dec_round)
            )
            buildable_info.append(self._makeentry(value=buildable_area, unit=far_unit, note=note, calc=calc))
        return sorted(buildable_info, key=lambda x: x["value"])

    def _zone_r(self, zone, attr, do_buildable=True, do_dwelling_units=True):
        """
        Retrieves data for Residential Base Zones in get()
        Municipal Code: Ch13, Art01, Div04
        """
        self.data["reference"] = "https://docs.sandiego.gov/municode/MuniCodeChapter13/Ch13Art01Division04.pdf"

        def _dwelling_units():
            """Populates base_density, base_dwelling_units, max_dwelling_units"""
            density_info = []
            density_units = ("sf per DU", "DU per lot")
            transit_note = "100% density bonus requires avg. unit size of 600 SF & max. unit size of 800 SF"

            density_info.append(self._default_density())
            self.data["density"] = density_info
            du_unit = "dwelling units"
            if density_info[0]["unit"] == density_units[1]:
                self.data["dwelling_units"] = [self._makeentry(density_info[0]["value"], du_unit, None, None)]
            elif attr["area"]:
                du_info = []
                density = density_info[0]["value"]
                num_units = attr["area"] / density
                units_calc = "{0} sf / {1} sf per DU = {2} -> {3} DUs".format(
                    attr["area"], density, num_units, math.ceil(num_units))
                du_info.append(self._makeentry(math.ceil(num_units), du_unit, None, units_calc))

                #check for affordable info
                base_units = du_info[0]["value"]
                affordable_dict = self._affordable(math.ceil(base_units),
                                                   self._coalesce(attr["transit_priority"], False))
                if affordable_dict:
                    max_units, market_units, affordable_units, num_incentives, annotation = 0, 1, 2, 3, 4
                    for income, data in affordable_dict.items():
                        annot = data[annotation].split(";")
                        calc = annot[1].strip()
                        note = annot[0].strip() + (("; " + transit_note) if attr["transit_priority"] else '')
                        du_info.append(self._makeentry(data[max_units], du_unit, note, calc))
                self.data["dwelling_units"] = sorted(du_info, key=lambda x: x["value"])

        def _buildable_area():
            far_info = [] #far info should be stored in a tuple of (value, notes, calc)
            far_unit = None

            if self._re_match("^RS-1-[234567]$", zone) and attr["area"]:
                far_note = "Sec 131.0446(a): Floor Area Ratio is based on the lot area in accordance with Table 131-04J."
                for row in self._get_table('131-04J', SanDiegoZoneQuery.tables):
                    if attr["area"]:
                        if float(row[0]) <= round(attr["area"]) <= float(row[1]):
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
                        #RT-zones have different FAR for 1-2 and 3 stories
                        far_info.append(self._makeentry(v['rule'], k, None))
            elif (self._re_match("RM-1-[23]", zone) or self._re_match("RM-2-[456]", zone) or
                    self._re_match("RM-3-[789]", zone) or self._re_match("RM-4-1[01]", zone)):
                far_info.append(self._default_far())
                if self._re_match("RM-1-[23]", zone) or self._re_match("RM-2-[456]", zone):
                    far_note = "1/4 of FAR reserved for required parking. [See Sec 131.0446(e)]"
                    req_parking = Fraction(1/4).limit_denominator(10)
                else: #self._re_match("RM-3-[789]", zone) or self._re_match("RM-4-1[01]", zone
                    far_note = "1/3 of buildable area reserved for required parking, unless developing Affordable Units"
                    req_parking = Fraction(1/3).limit_denominator(10)
                far = far_info[0]["value"] * (1 - req_parking)
                far_calc = "{0} FAR x {1} required parking = {2} FAR".format(far_info[0]["value"], 1 - req_parking, far)
                far_info.append(self._makeentry(far, far_unit, far_note, far_calc))
            elif zone == "RM-5-12":
                far_note = "Sec 131.0446(d): Floor area ratio for buildings exceeding 4 stories or 48 feet of" \
                           " structure height shall be increased in accordance with Table 131-04K"
                far_calc_base = "Buildings at least {0} floors or {1} feet"
                #if either floor or height specified, find one row in table 131-04K that fits,
                # otherwise append entire table
                if attr["floors"] or attr["height"]:
                    defaults = 1, 48, 1.80
                    curr_far = self._makeentry(defaults[0], far_unit, far_note, None)
                    for row in self._get_table("131-04K", SanDiegoZoneQuery.tables):
                        far_calc = far_calc_base.format(str(row[0]), str(row[1]))
                        if ((self._coalesce(attr["floors"], defaults[0]) >= row[0] or
                            self._coalesce(attr["height"], defaults[1]) >= row[1]) and
                            row[2] >= curr_far[0]):
                                curr_far = self._makeentry(row[2], far_unit, far_note, far_calc)
                    far_info.append(curr_far)
                else:
                    for row in self._get_table("131-04K", SanDiegoZoneQuery.tables):
                        far_calc = far_calc_base.format(str(row[0]), str(row[1]))
                        far_info.append(self._makeentry(row[2], far_unit, far_note, far_calc))
            else:
                far_info.append(self._default_far())

            far_info.sort(key=lambda x: x["value"])
            self.data["far"] = far_info

            if attr["area"]:
                buildable_info = []
                build_unit = "sf"
                for far in self.data["far"]:
                    far_val = far["value"]
                    buildable = far_val * attr["area"]
                    buildable_calc = "{0} FAR x {1} sf = {2} sf".format(far_val, attr["area"], buildable)
                    buildable_info.append(self._makeentry(buildable, build_unit, None, buildable_calc))
                self.data["buildable_area"] = buildable_info
        if do_dwelling_units: _dwelling_units()
        if do_buildable: _buildable_area()

    def _zone_c(self, zone, attr):
        self.data["reference"] = "https://docs.sandiego.gov/municode/MuniCodeChapter13/Ch13Art01Division05.pdf"
        decimals = self._coalesce(attr["decimals"], 2)
        def _dwelling_units():
            self.data["density"] = []
            if zone in ("CO-2-1", "CO-2-2", "CP-1-1"):
                self.data["density"].append(self._makeentry(value=None, unit=None,
                                                            note="Residential use not permitted.", calc=None))
            else:
                self.data["density"].append(self._default_density())
                if attr["area"]:
                    du_info = []
                    du_unit = "dwelling units"
                    density = self.data["density"][0]["value"]
                    note = "Base max dwelling units"
                    base_du = attr["area"] / density
                    calc = "{0} sf / {1} sf per DU = {2} -> {3} DU".format(attr["area"], density,
                                                                           round(base_du, 2), math.ceil(base_du))
                    du_info.append(self._makeentry(value=math.ceil(base_du), unit=du_unit, note=note, calc=calc))

                    #do affordable calculations
                    affordable = self._affordable(math.ceil(base_du), self._coalesce(attr["transit_priority"], False))
                    if affordable:
                        transit_note = "100% density bonus requires avg. unit size of 600 SF & max. unit size of 800 SF"
                        max_units, market_units, affordable_units, num_incentives, annotation = 0, 1, 2, 3, 4
                        for income, data in affordable.items():
                            annot = data[annotation].split(";")
                            calc = annot[1].strip()
                            note = annot[0].strip() + (("; " + transit_note) if attr["transit_priority"] else '')
                            du_info.append(self._makeentry(value=data[max_units], unit=du_unit, note=note, calc=calc))
                    self.data["dwelling_units"] = sorted(du_info, key=lambda x: x["value"])

        def _buildable_area():
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
            self.data["far"] = sorted(far_info, key=lambda x: x["value"])
            if attr["area"]:
                buildable_info = []
                build_unit = "sf"
                for f in self.data["far"]:
                    build_area = f["value"] * attr["area"]
                    build_note = f["note"]
                    build_calc = "{0} sf x {1} FAR = {2}".format(round(attr["area"], decimals),
                                                                 f["value"], round(build_area, decimals))
                    buildable_info.append(self._makeentry(value=round(build_area, decimals),
                                                          unit=build_unit, note=build_note, calc=build_calc))
                self.data["buildable_area"] = sorted(buildable_info, key=lambda x: x["value"])
        _dwelling_units()
        _buildable_area()

    def _zone_i(self, zone, attr):
        self.data["reference"] = "http://docs.sandiego.gov/municode/MuniCodeChapter13/Ch13Art01Division06.pdf"
        def _dwelling_units():
            if zone.startswith("IP-"):
                self.data["density"] = [self._default_density()]
                if attr["area"]:
                    transit_pr = self._coalesce(attr["transit_priority"], False)
                    self.data["dwelling_units"] = self._default_dwelling_units(area=attr["area"],
                                                                               density_info=self.data["density"],
                                                                               transit_priority=transit_pr)
            else:
                du_unit = "dwelling units"
                np_note = "Residential use not permitted"
                self.data["density"] = [self._makeentry(None, None, np_note, None)]
                self.data["dwelling_units"] = [self._makeentry(0, du_unit, np_note, None)]

        def _buildable_area():
            self.data["far"] = [self._default_far()]
            if attr["area"]:
                self.data["buildable_area"] = self._default_buildable_area(area=attr["area"],
                                                                           far_info=self.data["far_info"])
        _dwelling_units()
        _buildable_area()

    def _zone_o(self, zone, attr):
        self.data["reference"] = "TODO"

    def _zone_a(self, zone, attr):
        self.data["reference"] = "TODO"

    def _zone_cupd(self, zone, attr):
        self.data["reference"] = "https://docs.sandiego.gov/municode/MuniCodeChapter15/Ch15Art05Division02.pdf"
        def _dwelling_units():
            self.data["density"] = [self._default_density()]
            if attr["area"]:
                transit_priority = self._coalesce(attr["transit_priority"], False)
                self.data["dwelling_units"] = self._default_dwelling_units(
                    attr["area"], self.data["density"], transit_priority=transit_priority)

        def _buildable_area():
            max_far_key = "Max floor area ratio"
            bonus_far_key = "Mixed use bonus floor area ratio"
            min_res_key = "Min % to residential for mixed use bonus"
            base_far, bonus_far, min_res = None, None, None
            for k, v in self.data["dev_regulations"].items():
                if max_far_key.lower() in k.lower():
                    base_far = v['rule']
                    print(base_far)
                elif bonus_far_key.lower() in k.lower():
                    bonus_far = v['rule']
                    print(bonus_far)
                elif min_res_key.lower() in k.lower():
                    min_res = v['rule']
                    print(min_res)

            far_info = []
            far_unit = None
            far_info.append(self._makeentry(
                value=base_far, unit=far_unit,
                note="Base floor area ratio",
                calc=None))
            far_info.append(self._makeentry(
                value=bonus_far, unit=far_unit,
                note="Mixed use bonus floor area ratio; required min {0}% residential use".format(min_res),
                calc=None))
            far_info.append(self._makeentry(
                value=bonus_far + base_far, unit=far_unit,
                note="Max floor area ratio with mixed use bonus",
                calc=None))
            self.data["far_info"] = far_info

            if attr["area"]:
                self.data["buildable_area"] = self._default_buildable_area(attr["area"], self.data["far_info"])

        _dwelling_units()
        _buildable_area()

    def _zone_ccpd(self, zone, attr):
        self.data["reference"] = "https://docs.sandiego.gov/municode/MuniCodeChapter15/Ch15Art05Division02.pdf"

    def _zone_mx(self, zone, attr):
        self.data["reference"] = "https://docs.sandiego.gov/municode/MuniCodeChapter13/Ch13Art01Division07.pdf"
        def _buildable_area():
            pass

    def _affordable(self, base_units, transit_priority=False):
        """
        Ref: https://docs.sandiego.gov/municode/MuniCodeChapter14/Ch14Art03Division07.pdf
        Returns a dict showing maximum affordable density at each income level.
            If base_units not eligible for affordable bonus, returns an empty dict
            Each row is a tuple that contains:
                [0] max units
                [1] market-price units
                [2] affordable units
                [3] number of incentives
                [4] annotation
        """
        min_affordable = 5
        """
        Sec 143.0715: This Division applies to any development where current zoning allows for five
        or more dwelling units, not including density bonus units
        """
        results = {}
        if base_units >= min_affordable:
            """
            Incentives are not factored into calculations, as they must be applied for and processed separately 
            by the city. However if there is a tie in max units, the choice that yields more incentives is used.
            """
            affordable_tables = {
                "very low income": self._get_table("143-07A", SanDiegoZoneQuery.tables),
                "low income": self._get_table("143-07B", SanDiegoZoneQuery.tables),
                "moderate income": self._get_table("143-07C", SanDiegoZoneQuery.tables),
            }
            transit_bonus = 1 if transit_priority else 0

            def _is_better(units:tuple, affordable:tuple, incentives:tuple):
                """
                :param units: current units, new units
                :param affordable: current affordable_units, new affordable units
                :param incentives: current number of incentives, new number of incentives
                :return: True if new values yield better results, i.e.
                    * Yield at least as many units
                    * Yields at least as many incentives, given same units
                    * Requires less affordable, given same units and incentives
                """
                curr, new = 0, 1
                if units[curr] < units[new]:
                    return True
                elif units[curr] == units[new]:
                    if incentives[curr] < incentives[new]:
                        return True
                    elif incentives[curr] == incentives[new]:
                        if affordable[curr] > affordable[new]:
                            return True
                return False

            for income, table in affordable_tables.items():
                market_units = max_units = base_units + (1 + transit_bonus)
                affordable_units = 0
                num_incentives = 0
                min_affordable_perc = 0
                bonus_density_perc = 0
                for row in table:
                    curr_affordable_perc = row[0]
                    curr_bonus_density_perc = max(row[1], transit_bonus * 100)
                    curr_incentives = row[2]
                    curr_units = base_units + math.ceil(base_units * curr_bonus_density_perc / 100)
                    if _is_better((max_units, curr_units), (min_affordable_perc, curr_affordable_perc),
                                  (num_incentives, curr_incentives)):
                        min_affordable_perc = curr_affordable_perc
                        bonus_density_perc = curr_bonus_density_perc
                        num_incentives = curr_incentives
                        max_units = curr_units
                        affordable_units = math.ceil(base_units * min_affordable_perc / 100)
                        market_units = max_units - affordable_units

                annotation = "{0}% {8} = {1} Density Bonus and {2} Incentives; " \
                             "{3} x {4} = {5} Units ({6} Market rate, {7} {8})".format(
                    min_affordable_perc, bonus_density_perc, num_incentives, base_units, 1 + bonus_density_perc / 100,
                    max_units, market_units, affordable_units, income)
                results[income] = (max_units, market_units, affordable_units, num_incentives, annotation)
        return results