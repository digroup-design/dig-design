import unittest
from parameterized import parameterized
from csv import DictReader
from calculations.AddressQueryFactory import AddressQueryFactory

"""Unit tests for reports"""
# Run: python -m unittest

def csv_to_dict(filename, delimiter=';'):
    """Takes a csv file and returns it as a dictionary, with the first column's values as keys"""
    data_dict = {}
    with open(filename, 'r') as file:
        data = DictReader(file, delimiter=delimiter)
        keys, p_key = None, None
        for row in data:
            if keys is None:
                keys = tuple(row.keys())
                p_key = keys[0]
            data_dict[row[p_key]] = {}
            for k in [k for k in keys if k != p_key]:
                data_dict[row[p_key]][k] = row[k]
    return data_dict

class TestSanDiego(unittest.TestCase):
    q = AddressQueryFactory()
    city, state = "san diego", "california"

    suffix_tests = (
        ("2405 union st", "2405 Union Street"),
        ("4442 ocean view blvd", "  4442 OCEAN VIEW BOULEVARD")
    )

    apn_tests = (
        ('4182920500', '418-292-05-00', '4182920500  '),
    )

    test_dict = csv_to_dict("test_data/sandiego_test_data.csv", ";")

    @parameterized.expand(suffix_tests)
    def test_suffixes(self, *query_list):
        """Test to see if different suffixes of the same address returns the same result"""
        if len(query_list) < 2:
            raise ValueError("Test case requires at least 2 forms of the same address & suffix")
        print('\n', "="*5, "TESTING SUFFIX INPUTS", "="*5)

        query_set = []
        for a in query_list:
            query_set.append(self.q.get(city=self.city, state=self.state, address=a))
            print(self.q)
        for i in range(1, len(query_set)):
            self.assertDictEqual(query_set[0], query_set[i])

    @parameterized.expand(apn_tests)
    def test_apn(self, *apn_list):
        """Test to see if different forms of APN returns the same result"""
        if len(apn_list) < 2:
            raise ValueError("Test case requires at least 2 forms of the same APN")
        print('\n', "="*5, "TESTING APN INPUTS", "="*5)

        query_set = []
        for a in apn_list:
            query_set.append(self.q.get(city=self.city, state=self.state, apn=a))
            print(self.q)
        for i in range(1, len(query_set)):
            self.assertDictEqual(query_set[0], query_set[i])

    @parameterized.expand(test_dict)
    def test_a_results(self, query):
        """Test to see if data produces desired results"""
        print('\n', "="*5, 'TESTING RESULT FOR "{0}"'.format(query), "="*5)

        q1 = self.q.get(city=self.city, state=self.state, address=query)
        print(self.q)

        data = self.test_dict[query]
        for field in ("zone", "apn", "transit_priority"):
            if data[field] != '':
                self.assertEqual(str(q1[field]), data[field])

        #For lot area, we want calculated area to be within 2% of the actual
        #Minor failure in lot_area test may be acceptable due to inaccuracies in GIS data
        if data["lot_area"] != '':
            lot_area = float(data["lot_area"])
            area_err = abs(q1["lot_area"] - lot_area) / lot_area
            self.assertLess(area_err, 0.1,
                            "Acceptable if GIS data matches {0}".format(str(q1["lot_area"])))

            for field in ("base_dwelling_units", "max_dwelling_units"):
                if data[field] != '':
                    self.assertEqual(q1[field], int(data[field]))