from calculations.San_Diego.SanDiegoZoneQuery import SanDiegoZoneQuery

class SanDiegoZoneO(SanDiegoZoneQuery):

    def _get_reference(self) ->str:
        return "https://docs.sandiego.gov/municode/MuniCodeChapter13/Ch13Art01Division02.pdf"

    def _get_density(self):
        if "OR-" in self.data["zone"]:
            return super()._get_density()
        else:
            return [self._makeentry(0, "DU per lot", "Residential use not permitted", None)]

    def _get_far(self):
        if "OR-" in self.data["zone"]:
            return super()._get_far()
        else:
            return [self._makeentry(0, None, "Development not permitted", None)]