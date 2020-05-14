from calculations.San_Diego.SanDiegoZoneQuery import SanDiegoZoneQuery

class SanDiegoZoneMX(SanDiegoZoneQuery):
    du_unit = "dwelling units"

    def _get_reference(self) -> str:
        return "https://docs.sandiego.gov/municode/MuniCodeChapter13/Ch13Art01Division07.pdf"

    def _get_density(self):
        #TODO
        return None

    def _get_buildable_area(self) ->list:
        return None