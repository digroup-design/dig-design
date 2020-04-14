import unittest
from calculations.AddressQueryFactory import AddressQueryFactory

"""Unit tests for reports"""
# Run: python -m unittest

class TestSanDiego(unittest.TestCase):
    q = AddressQueryFactory()
    city, state = "san diego", "california"
    def test_suffixes(self):
        """Test to see if different suffixes of the same address returns the same result"""
        addr1 = ("2405 union st", "2405 Union Street")
        addr2 = ("4442 ocean view blvd", "  4442 OCEAN VIEW BOULEVARD")
        for addr in (addr1, addr2):
            q1 = self.q.get(city=self.city, state=self.state, address=addr[0])
            print(self.q)
            q2 = self.q.get(city=self.city, state=self.state, address=addr[1])
            print(self.q)
            self.assertDictEqual(q1, q2)

    def test_apn(self):
        """Test to see if different forms of APN returns the same result"""
        apn = ('4182920500', '418-292-05-00', '4182920500  ')
        q1 = self.q.get(city=self.city, state=self.state, apn=apn[0])
        print(self.q)
        q2 = self.q.get(city=self.city, state=self.state, apn=apn[1])
        print(self.q)
        q3 = self.q.get(city=self.city, state=self.state, apn=apn[2])
        print(self.q)
        self.assertDictEqual(q1, q2)
        self.assertDictEqual(q1, q3)

    def test_results(self):
        """Test to see if data produces desired results"""
        addr = "3901 clairemont dr"
        zone = "CN-1-2"
        apn = "4182920500"
        area_sf = 17751.11

        q1 = self.q.get(city=self.city, state=self.state, address=addr)
        print(self.q)
        self.assertEqual(q1["zone"], zone)
        self.assertEqual(q1["apn"], apn)
        #For lot area, we want calculated area to be within 2% of the actual
        area_err = abs(q1["lot_area"] - area_sf) / area_sf
        self.assertLessEqual(area_err, 0.02)
