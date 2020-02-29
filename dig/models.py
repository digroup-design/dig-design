from django.db import models
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dig.settings')
#django.setup()

class Address(models.Model):
    number = models.CharField(max_length=10)
    unit = models.CharField(max_length=20, null=True)
    street_name = models.CharField(max_length=30, null=True)
    street_sfx = models.CharField(max_length=20, null=True)
    city = models.CharField(max_length=20, null=True)
    state = models.CharField(max_length=10, null=True)
    zip = models.CharField(max_length=20, null=True)
    apn = models.CharField(max_length=20, null=True)
    parcel_id = models.CharField(max_length=10, null=True)

    def __str__(self):
        join_str = [str(s) for s in [self.number, self.street_name, self.street_sfx, self.unit] if s is not None]
        return ' '.join(join_str)

    class Meta:
        abstract = True

class Parcel(models.Model):
    parcel_id = models.CharField(max_length=10) #TODO: db_index = True
    lot_area = models.CharField(max_length=20)
    lot_length = models.CharField(max_length=20, null=True)
    geometry = models.TextField()

    def __str__(self):
        return self.parcel_id

    class Meta:
        abstract = True

class Zone(models.Model):
    name = models.CharField(max_length=50)
    geometry = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        abstract = True

#for San Diego
class SanDiego_Address(Address):
    pass

class SanDiego_Parcel(Parcel):
    apn = models.CharField(max_length=20, null=True)
    owner1 = models.CharField(max_length=100, null=True)
    owner2 = models.CharField(max_length=100, null=True)
    owner3 = models.CharField(max_length=100, null=True)
    owner_address_1 = models.CharField(max_length=100, null=True)
    owner_address_2 = models.CharField(max_length=100, null=True)
    owner_address_3 = models.CharField(max_length=100, null=True)
    owner_address_4 = models.CharField(max_length=100, null=True)
    owner_zip = models.CharField(max_length=20, null=True)
    number = models.CharField(max_length=10, null=True)
    street_name = models.CharField(max_length=20, null=True)
    street_sfx = models.CharField(max_length=10, null=True)
    city = models.CharField(max_length=20, null=True)
    zip = models.CharField(max_length=20, null=True)
    legal_desc = models.CharField(max_length=100, null=True)
    asr_land = models.CharField(max_length=20, null=True)
    asr_impr = models.CharField(max_length=20, null=True)

    def __str__(self):
        join_str = [str(self.number), str(self.street_name), str(self.street_sfx)]
        join_str = [s for s in join_str if s is not None]
        return '{0}: {1}'.format(self.parcel_id, ' '.join(join_str))

class SanDiego_Zone(Zone):
    imp_date = models.CharField(max_length=20, null=True)

class SanDiego_TransitArea(Zone):
    pass
