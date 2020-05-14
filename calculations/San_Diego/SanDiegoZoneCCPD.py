from calculations.San_Diego.SanDiegoZoneQuery import SanDiegoZoneQuery

class SanDiegoZoneCCPD(SanDiegoZoneQuery):
    def _get_reference(self) -> str:
        return "https://docs.sandiego.gov/municode/MuniCodeChapter15/Ch15Art05Division02.pdf"

