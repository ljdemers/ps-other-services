"""Screening Workers country sanctions enums module"""
from enum import Enum


class ShipCountryType(Enum):

    COUNTRY_OF_DOMICILE = 'country_of_domicile'
    COUNTRY_OF_CONTROL = 'country_of_control'
    COUNTRY_OF_REGISTRATION = 'country_of_registration'
