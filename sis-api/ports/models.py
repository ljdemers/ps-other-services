from django.db import models
from django.db.models import Q


class Country(models.Model):

    class Meta:
        ordering = ('name',)
        verbose_name_plural = "countries"

    code = models.CharField(primary_key=True, max_length=3)
    name = models.CharField(max_length=64, unique=True)
    world_region = models.CharField(max_length=32, null=True, blank=True)
    world_continent = models.CharField(max_length=16, null=True, blank=True)
    flag_registry = models.IntegerField(null=True, blank=True)
    flag_lrit_identifier = models.IntegerField(null=True, blank=True)
    flag_name = models.CharField(max_length=128, null=True, blank=True)
    iso_3166_1_alpha_2 = models.CharField(max_length=50, null=True, blank=True)

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.code)

    @classmethod
    def lookup(cls, **data):
        """
        Look up a country based on parameters provided. If using name for lookup, the primary
        country name will be used first to find a unique match. If this fails, the alternate names
        are also used.

        :param code: Country code for lookup. This is the most reliable method of locating a country.
        :param name: Name of the country.
        :return: A single country which matches the criteria.
        """
        code = data.get('code', '').strip()
        name = data.get('name', '').strip()
        if code:
            return cls.objects.get(code__iexact=code)
        if name:
            return cls.objects.get(Q(name__iexact=name) | Q(alternate_names__name__iexact=name))
        return None


class CountryAlternateName(models.Model):

    class Meta:
        verbose_name = "alternate name"
        verbose_name_plural = "alternate names"

    country = models.ForeignKey(Country, null=False, blank=False, related_name='alternate_names', on_delete=models.CASCADE)
    name = models.CharField(max_length=64, unique=True)


class Port(models.Model):

    class Meta:
        ordering = ('name',)
        #unique_together = ('country', 'name')

    code = models.CharField(max_length=8, primary_key=True)
    name = models.CharField(max_length=64)
    country = models.ForeignKey(Country, null=False, blank=False, default="1", on_delete=models.CASCADE)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    scale = models.FloatField(null=True, blank=True)  # In degrees
    #polygon = models.PolygonField(null=True, blank=True)

    def __unicode__(self):
        return '%s (%s) - %s' % (self.name, self.code, self.country)

    @classmethod
    def lookup(cls, **data):
        """
        Look up a port based on parameters provided. If using name for lookup, the primary
        port name will be used first to find a unique match. If this fails, the alternate names
        are also used.

        :param code: Port code for lookup. This is the most reliable method of locating a port.
        :param name: Name of the port. This must be combined with a country for uniqueness.
        :param country: Name of the country. This will only be used in conjunction with name.
        :return: A single port which matches the criteria.
        """
        code = data.get('code', '').strip()
        name = data.get('name', '').strip()
        country = data.get('country', '').strip()
        if code:
            return cls.objects.get(code__iexact=code)
        if name:
            country = Country.lookup(name=country)
            try:
                return cls.objects.get(name__iexact=name, country=country)
            except cls.DoesNotExist:
                return cls.objects.get(alternate_names__name__iexact=name, alternate_names__country=country)
        return cls.objects.get(**data)


class PortAlternateName(models.Model):

    class Meta:
        unique_together = ('country', 'name')
        verbose_name = "alternate name"
        verbose_name_plural = "alternate names"

    port = models.ForeignKey(Port, null=False, blank=False, related_name='alternate_names', on_delete=models.CASCADE)
    country = models.ForeignKey(Country, null=False, blank=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
