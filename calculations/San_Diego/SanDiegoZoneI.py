from calculations.San_Diego.SanDiegoZoneQuery import SanDiegoZoneQuery

class SanDiegoZoneI(SanDiegoZoneQuery):
    def _get_reference(self) ->str:
        return "http://docs.sandiego.gov/municode/MuniCodeChapter13/Ch13Art01Division06.pdf"

    def _get_density(self):
        zone = self.data["zone"]
        if zone.startswith("IP-"):
            return super()._get_density()
        else:
            np_note = "Residential use not permitted"
            return [self._makeentry(None, None, np_note, None)]

    def _get_dwelling_units(self):
        zone = self.data["zone"]
        if zone.startswith("IP-"):
            return super()._get_dwelling_units()
        else:
            du_unit = "dwelling units"
            np_note = "Residential use not permitted"
            return [self._makeentry(0, du_unit, np_note, None)]

    #FAR and buildable area calculations use default implementations