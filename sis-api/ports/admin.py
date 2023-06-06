""" Admin classes for the ports application. """
from django.contrib import admin
from ports import models


class PortAltNames(admin.TabularInline):
    """ Inline table display of alternate names for a port. """
    model = models.PortAlternateName
    original = False
    show_url = False


class PortAdmin(admin.ModelAdmin):
    """ Admin screen for editing port information. """
    list_display = ('code', 'name', 'country')
    list_display_links = ('code', 'name')
    list_filter = ('country',)
    search_fields = ('name',)
    readonly_fields = ('code',)
    inlines = (PortAltNames,)


class CountryAltNames(admin.TabularInline):
    """ Inline table display of alternate names for a country. """
    model = models.CountryAlternateName
    original = False
    show_url = False


class CountryAdmin(admin.ModelAdmin):
    """ Admin screen for editing country information. """
    list_display = ('code', 'name', 'world_continent')
    list_display_links = ('code', 'name')
    list_filter = ('world_continent',)

    search_fields = ('name',)
    readonly_fields = ('code',)
    inlines = (CountryAltNames,)

admin.site.register(models.Port, PortAdmin)

admin.site.register(models.Country, CountryAdmin)
