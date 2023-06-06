"""Screening API ships models module"""
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, String, Numeric, Date

from screening_api.screenings.enums import Severity
from screening_api.models import BaseModel
from screening_api.ships.enums import ShipAssociateType, ShipCountryType
from screening_api.ships.mixins import ShipAssociateMixin


class Ship(ShipAssociateMixin, BaseModel):

    __tablename__ = 'ships'

    imo = Column(String, nullable=False, unique=True)
    imo_id = Column(Integer, nullable=False, unique=True)
    mmsi = Column(String)
    type = Column(String, index=True)
    name = Column(String)
    call_sign = Column(String)
    status = Column(String)
    port_of_registry = Column(String)
    classification_society = Column(String)
    deadweight = Column(Integer)
    breadth = Column(Numeric)
    displacement = Column(Integer)
    draught = Column(Numeric)
    build_country_name = Column(String)
    build_year = Column(Integer)
    shipbuilder = Column(String)
    pandi_club = Column(String)
    weight = Column(Integer)
    length = Column(Numeric)

    safety_management_certificate_doc_company = Column(String)
    safety_management_certificate_date_issued = Column(Date)

    country_id = Column(String, index=True)  # iso_3166_1_alpha_2
    country_name = Column(String)
    country_effective_date = Column(String)

    registered_owner = Column(String)
    registered_owner_company_id = Column(
        Integer,
        ForeignKey(
            'sis_companies.id',
            onupdate="CASCADE", ondelete="CASCADE",
        ),
        nullable=True,
    )
    registered_owner_company_code = Column(String)
    registered_owner_country_of_domicile = Column(String)
    registered_owner_country_of_control = Column(String)
    registered_owner_country_of_registration = Column(String)
    operator = Column(String)
    operator_company_id = Column(
        Integer,
        ForeignKey(
            'sis_companies.id',
            onupdate="CASCADE", ondelete="CASCADE",
        ),
        nullable=True,
    )
    operator_company_code = Column(String)
    operator_country_of_domicile = Column(String)
    operator_country_of_control = Column(String)
    operator_country_of_registration = Column(String)
    group_beneficial_owner = Column(String)
    group_beneficial_owner_company_id = Column(
        Integer,
        ForeignKey(
            'sis_companies.id',
            onupdate="CASCADE", ondelete="CASCADE",
        ),
        nullable=True,
    )
    group_beneficial_owner_company_code = Column(String)
    group_beneficial_owner_country_of_domicile = Column(String)
    group_beneficial_owner_country_of_control = Column(String)
    group_beneficial_owner_country_of_registration = Column(String)
    ship_manager = Column(String)
    ship_manager_company_id = Column(
        Integer,
        ForeignKey(
            'sis_companies.id',
            onupdate="CASCADE", ondelete="CASCADE",
        ),
        nullable=True,
    )
    ship_manager_company_code = Column(String)
    ship_manager_country_of_domicile = Column(String)
    ship_manager_country_of_control = Column(String)
    ship_manager_country_of_registration = Column(String)
    technical_manager = Column(String)
    technical_manager_company_id = Column(
        Integer,
        ForeignKey(
            'sis_companies.id',
            onupdate="CASCADE", ondelete="CASCADE",
        ),
        nullable=True,
    )
    technical_manager_company_code = Column(String)
    technical_manager_country_of_domicile = Column(String)
    technical_manager_country_of_control = Column(String)
    technical_manager_country_of_registration = Column(String)

    registered_owner_company = relationship(
        "SISCompany",
        foreign_keys=[registered_owner_company_id],
    )
    operator_company = relationship(
        "SISCompany",
        foreign_keys=[operator_company_id],
    )
    group_beneficial_owner_company = relationship(
        "SISCompany",
        foreign_keys=[group_beneficial_owner_company_id],
    )
    ship_manager_company = relationship(
        "SISCompany",
        foreign_keys=[ship_manager_company_id],
    )
    technical_manager_company = relationship(
        "SISCompany",
        foreign_keys=[technical_manager_company_id],
    )

    def __json__(self):
        return ['imo_id', 'type', 'name', 'country_id', 'country_name']

    def get_company(self, associate_type: ShipAssociateType):
        field_name = self.get_company_field_name(associate_type)
        return getattr(self, field_name)

    def get_company_id(self, associate_type: ShipAssociateType) -> str:
        field_name = self.get_company_id_field_name(associate_type)
        return getattr(self, field_name)

    def get_company_name(self, associate_type: ShipAssociateType) -> str:
        field_name = self.get_company_name_field_name(associate_type)
        return getattr(self, field_name)

    def get_country_of_domicile(
            self, associate_type: ShipAssociateType) -> str:
        return self.get_country_name(
            associate_type, ShipCountryType.COUNTRY_OF_DOMICILE)

    def get_country_of_control(self, associate_type: ShipAssociateType) -> str:
        return self.get_country_name(
            associate_type, ShipCountryType.COUNTRY_OF_CONTROL)

    def get_country_of_registration(
            self, associate_type: ShipAssociateType) -> str:
        return self.get_country_name(
            associate_type, ShipCountryType.COUNTRY_OF_REGISTRATION)

    def get_country_name(
        self,
        associate_type: ShipAssociateType,
        country_type: ShipCountryType,
    ) -> str:
        field_name = self.get_country_field_name(associate_type, country_type)
        return getattr(self, field_name)

    def get_company_ids(self):
        ids = []
        for name, associate_type in ShipAssociateType.__members__.items():
            company_id = self.get_company_id(associate_type)
            if company_id is not None:
                ids.append(company_id)

        return ids

    @property
    def build_age(self):
        year_now = datetime.utcnow().year
        return year_now - int(self.build_year)

    @property
    def build_age_severity(self):
        age_severity = Severity.OK
        if self.build_age >= 25:
            age_severity = Severity.CRITICAL
        elif 25 > self.build_age >= 15:
            age_severity = Severity.WARNING
        return age_severity

    @property
    def flag_effective_date(self):
        effective_date = self.country_effective_date
        flag_date = effective_date[0:4] + '-' + effective_date[4:6]
        return flag_date
