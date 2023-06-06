from screening_workers.country_sanctions.enums import ShipCountryType


class ShipAssociatedCountriesMixin:

    def __init__(self, ship):
        self.ship = ship

    def get_company(self, associate_name: str) -> str:
        return getattr(self.ship, associate_name)

    def get_country_of_domicile(self, associate_name: str) -> str:
        return self.get_country_name(
            associate_name, ShipCountryType.COUNTRY_OF_DOMICILE)

    def get_country_of_control(self, associate_name: str) -> str:
        return self.get_country_name(
            associate_name, ShipCountryType.COUNTRY_OF_CONTROL)

    def get_country_of_registration(self, associate_name: str) -> str:
        return self.get_country_name(
            associate_name, ShipCountryType.COUNTRY_OF_REGISTRATION)

    def get_country_name(
            self, associate_name: str, country_type: ShipCountryType) -> str:
        country_field_name = self.get_country_field_name(
            associate_name, country_type)
        return getattr(self.ship, country_field_name)

    @classmethod
    def get_country_field_name(
            cls, associate_name: str, country_type: ShipCountryType) -> str:
        return '_'.join([associate_name, country_type.value])
