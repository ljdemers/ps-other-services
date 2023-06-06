from screening_api.ships.enums import ShipAssociateType, ShipCountryType


class ShipAssociateMixin:

    @staticmethod
    def get_country_field_name(
        associate_type: ShipAssociateType,
        country_type: ShipCountryType,
    ) -> str:
        return '_'.join([associate_type.value, country_type.value])

    @staticmethod
    def get_company_name_field_name(associate_type: ShipAssociateType):
        return associate_type.value

    @staticmethod
    def get_company_field_name(associate_type: ShipAssociateType):
        return '_'.join([associate_type.value, 'company'])

    @staticmethod
    def get_company_id_field_name(associate_type: ShipAssociateType):
        return '_'.join([associate_type.value, 'company_id'])

    @staticmethod
    def get_company_code_field_name(associate_type: ShipAssociateType):
        return '_'.join([associate_type.value, 'company_code'])
