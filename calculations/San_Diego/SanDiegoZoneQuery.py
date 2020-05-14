from calculations.ZoneQuery import ZoneQuery
from shapely.geometry import shape

import math

class SanDiegoZoneQuery(ZoneQuery):
    """
    Data from: https://www.sandiego.gov/city-clerk/officialdocs/municipal-code/chapter-13
    """
    MIN_AFFORDABLE = 5
    use_regs = "sandiego_regulations_use"
    dev_regs = "sandiego_regulations_dev"
    tables = "sandiego_regulations_tables"

    transit_note = "100% density bonus requires avg. unit size of 600 SF & max. unit size of 800 SF"
    du_unit = "dwelling units"
    decimals = 2

    def get(self, zone:str, area:float=None, geometry:dict=None, transit_priority=False,
            stories:int=None, attached:bool=False, decimals:int=2)->dict:
        """
        :param zone: (str, optional)
        :param area: (float, optional)
        :param geometry: (dict, optional)
        :param transit_priority: (bool, optional)
        :param stories: (int, optional)
        :param attached: (book, optional)
        :param decimals: (int, optional)
        :return: data (dict)
        """
        self.decimals = decimals
        self.data["zone"] = zone.upper()
        self.data["geometry"] = geometry
        self.data["area"] = shape(geometry).area if (area is None and geometry is not None) else area
        self.data["transit_priority"] = transit_priority
        self.data["stories"] = stories
        self.data["attached"] = attached
        self.data["reference"] = self._get_reference()

        self.data["dev_regulations"], self.data["use_regulations"] = self._get_reg_dicts(zone)
        self.data["density"] = self._get_density()
        self.data["far"] = self._get_far()
        self.data["buildable_area"] = self._get_buildable_area()
        self.data["dwelling_units"] = self._get_dwelling_units()

        return self.data

    def _get_reg_dicts(self, zone)->tuple:
        """default implementation for retrieving regulation data"""
        dev_regs = self._find_regs(zone, SanDiegoZoneQuery.dev_regs)
        use_regs = self._find_regs(zone, SanDiegoZoneQuery.use_regs)
        if None in (dev_regs, use_regs):
            raise ValueError("Data for {0} not found.".format(zone))
        return dev_regs, use_regs

    def _get_far(self)->list:
        """default implementation of finding FAR"""
        for k, v in self.data['dev_regulations'].items():
            if self._re_match(".*floor.*area.*ratio.*", k.lower()):
                return [self._makeentry(value=v['rule'], unit=None, note=k, calc=None)]

    def _get_density(self)->list:
        """default implementation of finding permitted density"""
        for k, v in self.data['dev_regulations'].items():
            if self._re_match("max.* density", k.lower()):
                if self._re_match(".*(.*du .* lot.*).*", k.lower()):
                    density_unit = "DU per lot"
                else:
                    density_unit = "sf per DU"
                return [self._makeentry(value=v['rule'], unit=density_unit, note=k, calc=None)]

    def _get_dwelling_units(self)->list:
        """
        default implementation of finding possible numbers of dwelling units
        :return: list of dwelling units calculations in ascending order
        """
        du_info = []
        du_unit = self.du_unit
        area_unit = "sf"
        dec_round = self.decimals
        area = self.data["area"]
        density_info = self.data["density"]
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

        if len(du_info)> 0:
            transit_priority = self.data["transit_priority"]
            transit_note = self.transit_note

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

    def _get_buildable_area(self)->list:
        area = self.data["area"]
        if area is None: return None
        far_info = self.data["far"]

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

    def _get_lot_dimensions(self)->list:
        raise NotImplementedError

    def _get_height(self, area:float)->list:
        raise NotImplementedError

    def _get_setbacks(self)->list:
        raise NotImplementedError

    def _get_reference(self)->str:
        raise NotImplementedError

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
        min_affordable = self.MIN_AFFORDABLE
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