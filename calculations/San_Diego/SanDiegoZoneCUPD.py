from calculations.San_Diego.SanDiegoZoneQuery import SanDiegoZoneQuery

class SanDiegoZoneCUPD(SanDiegoZoneQuery):
    def _get_reference(self) -> str:
        return "https://docs.sandiego.gov/municode/MuniCodeChapter15/Ch15Art05Division02.pdf"

    def _get_reg_dicts(self, zone)->tuple:
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
                if zone == r[0]:
                    cond = True #TODO: write logic for conditions, using r[2] and r[4]
                    zone = r[1] if cond else r[3]
                #TODO: logic for Table 155-02A
        return super()._get_reg_dicts(zone)

    #Density, Dwelling Units, and Buildable Area use default implementations

    def _get_buildable_area(self):
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
        return far_info