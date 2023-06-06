from enum import Enum


class ShipAssociateType(Enum):

    GROUP_BENEFICIAL_OWNER = 'group_beneficial_owner'
    OPERATOR = 'operator'
    REGISTERED_OWNER = 'registered_owner'
    SHIP_MANAGER = 'ship_manager'
    TECHNICAL_MANAGER = 'technical_manager'


class ShipCountryType(Enum):

    COUNTRY_OF_DOMICILE = 'country_of_domicile'
    COUNTRY_OF_CONTROL = 'country_of_control'
    COUNTRY_OF_REGISTRATION = 'country_of_registration'
