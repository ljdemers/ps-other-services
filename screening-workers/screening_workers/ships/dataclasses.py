from screening_api.ships.enums import ShipAssociateType
from screening_api.ships.mixins import ShipAssociateMixin


class ShipData(dict, ShipAssociateMixin):

    def get_company_code(self, associate_type: ShipAssociateType) -> str:
        field_name = self.get_company_code_field_name(associate_type)
        return self[field_name]

    def get_company_name(self, associate_type: ShipAssociateType) -> str:
        field_name = self.get_company_name_field_name(associate_type)
        return self[field_name]

    def set_company_id(
        self, associate_type: ShipAssociateType, company_id: int,
    ) -> None:
        field_name = self.get_company_id_field_name(associate_type)
        self[field_name] = company_id
