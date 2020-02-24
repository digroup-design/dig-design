try:
    import calculations.Calculator as Calculator
    import calculations.GISReader as GISReader
except ModuleNotFoundError:
    import Calculator
    import GISReader

class CalculatorSanDiego(Calculator.Calculator):
    #all implementations in Calculator class designed to work by default for San Diego
    # def __init__(self, name):
    #     super().__init__(name)
    pass

class GISSanDiego(GISReader.GisDB):
    def get_address_feature(self, address):
        return self.get_feature('Address_APN', 'ADDRNMBR', address, 'ADDRNAME', '', 'ADDRSFX', '', concat=True)

    def get_address_proper(self, address):
        address_feature = self.get_address_feature(address)
        if address_feature is None:
            return None
        else:
            street_num = str(address_feature['properties']['ADDRNMBR']).replace('.0', '')
            street_name = address_feature['properties']['ADDRNAME']
            street_sfx = address_feature['properties']['ADDRSFX']
            street_full = ' '.join(filter(None, [street_num, street_name, street_sfx])).title()
            city = address_feature['properties']['COMMUNITY']
            zip = str(address_feature['properties']['ADDRZIP'])
            city_zip = '{0}, CA {1}'.format(city, zip)
            return [street_full, city_zip]

    def address_to_apn(self, address):
        return self.get_attr('Address_APN', 'APN', 'ADDRNMBR', address, 'ADDRNAME', '', 'ADDRSFX', '', concat=True)

    def address_to_parcel(self, address):
        return self.get_attr('Address_APN', 'PARCELID', 'ADDRNMBR', address, 'ADDRNAME', '', 'ADDRSFX', '', concat=True)

    def apn_to_parcel(self, apn):
        return self.get_attr('Address_APN', 'PARCELID', 'APN', apn)

    def address_to_parcel_feature(self, address):
        parcel_id = self.address_to_parcel(address)
        print('Parcel ID found: {0}'.format(parcel_id))

        file_id = 'Parcels[{0}]'.format(str(parcel_id)[0])
        print("Searching in {0}".format(file_id))
        return self.get_feature(file_id, 'PARCELID', parcel_id)

san_diego = CalculatorSanDiego("San Diego")

san_diego_gis = GISSanDiego("San Diego")

# def test():
#     parcel = san_diego_gis.address_to_parcel_feature("2405 union st")
#     geometry = parcel['geometry']
#     print(san_diego_gis.get_zones_dict('ZONING_BASE_SD', geometry))
#     print(san_diego_gis.intersects_zone('transit', geometry))