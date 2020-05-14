from calculations.San_Diego.SanDiegoZoneQuery import SanDiegoZoneQuery

class SanDiegoZoneA(SanDiegoZoneQuery):

    def _get_reference(self) ->str:
        return "https://docs.sandiego.gov/municode/MuniCodeChapter13/Ch13Art01Division03.pdf"