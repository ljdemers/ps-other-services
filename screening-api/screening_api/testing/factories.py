"""Screening API testing factories module"""
from datetime import date, datetime, timedelta
from random import randint, getrandbits

from factory import lazy_attribute
from factory.alchemy import SQLAlchemyModelFactory
from factory.declarations import LazyAttribute, LazyFunction
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice
from sqlalchemy.orm import Session

from screening_api.blacklisted_countries.models import BlacklistedCountry
from screening_api.blacklisted_sanctions.models import BlacklistedSanctionList
from screening_api.companies.models import (
    SISCompany, SISComplianceAssociation,
)
from screening_api.company_associations.models import CompanyAssociation
from screening_api.entities.enums import EntityType
from screening_api.entities.models import ComplianceEntity
from screening_api.sanctions.models import (
    ComplianceEntitySanction, ComplianceSanction,
)
from screening_api.screenings.enums import Severity, SeverityChange, Status
from screening_api.screenings.models import Screening
from screening_api.screenings_bulk.enums import BulkScreeningStatus
from screening_api.screenings_bulk.models import BulkScreening
from screening_api.screenings_history.models import ScreeningHistory
from screening_api.screenings_reports.models import ScreeningReport
from screening_api.ship_inspections.models import ShipInspection
from screening_api.ship_sanctions.models import ShipSanction
from screening_api.ships.models import Ship
from screening_api.testing.providers import ReportsProvider, ShipProvider


Faker.add_provider(ReportsProvider)
Faker.add_provider(ShipProvider)


class BaseModelFactory(SQLAlchemyModelFactory):

    created = LazyFunction(lambda: datetime.utcnow())
    updated = LazyFunction(lambda: datetime.utcnow())

    class Meta:
        abstract = True

    @classmethod
    def bind(cls, session):
        cls._meta.sqlalchemy_session = session
        return cls


class BlacklistedCountryFactory(BaseModelFactory):

    country_id = Faker('country_code')
    country_name = Faker('country')
    severity = FuzzyChoice(Severity)

    class Meta:
        model = BlacklistedCountry
        sqlalchemy_session_persistence = 'flush'


class ShipFactory(BaseModelFactory):

    imo = LazyAttribute(lambda x: str(x.imo_id))
    imo_id = Faker('random_int', max=9999999)
    type = FuzzyChoice(['Bulk Carrier', 'Crude Oil Tanker'])
    name = Faker('military_ship')
    call_sign = Faker('ship_call_sign')
    status = Faker('ship_status')
    port_of_registry = Faker('company')
    classification_society = Faker('company')
    deadweight = Faker('pyint')
    breadth = Faker('pydecimal')
    displacement = Faker('pyint')
    draught = Faker('pydecimal')
    build_country_name = Faker('country')
    build_year = Faker('year')
    shipbuilder = Faker('company')
    pandi_club = Faker('company')
    weight = Faker('pyint')
    length = Faker('pydecimal')

    safety_management_certificate_doc_company = Faker('company')
    safety_management_certificate_date_issued = Faker('past_date')

    country_id = Faker('country_code')
    country_name = Faker('country')
    country_effective_date = Faker('date', pattern='%Y%m')

    registered_owner = Faker('company')
    registered_owner_country_of_domicile = Faker('country')
    registered_owner_country_of_control = Faker('country')
    registered_owner_country_of_registration = Faker('country')
    operator = Faker('company')
    operator_country_of_domicile = Faker('country')
    operator_country_of_control = Faker('country')
    operator_country_of_registration = Faker('country')
    group_beneficial_owner = Faker('company')
    group_beneficial_owner_country_of_domicile = Faker('country')
    group_beneficial_owner_country_of_control = Faker('country')
    group_beneficial_owner_country_of_registration = Faker('country')
    ship_manager = Faker('company')
    ship_manager_country_of_domicile = Faker('country')
    ship_manager_country_of_control = Faker('country')
    ship_manager_country_of_registration = Faker('country')
    technical_manager = Faker('company')
    technical_manager_country_of_domicile = Faker('country')
    technical_manager_country_of_control = Faker('country')
    technical_manager_country_of_registration = Faker('country')

    class Meta:
        model = Ship
        sqlalchemy_session_persistence = 'flush'

    @lazy_attribute
    def mmsi(self):
        number = Faker('random_int', min=100000000, max=999999999).generate({})

        return str(number)

    @lazy_attribute
    def registered_owner_company_code(self):
        if self.registered_owner is None:
            return None

        number = Faker('random_int', min=1000000, max=9999999).generate({})
        return str(number)

    @lazy_attribute
    def operator_company_code(self):
        if self.operator is None:
            return None

        number = Faker('random_int', min=1000000, max=9999999).generate({})
        return str(number)

    @lazy_attribute
    def group_beneficial_owner_company_code(self):
        if self.group_beneficial_owner is None:
            return None

        number = Faker('random_int', min=1000000, max=9999999).generate({})
        return str(number)

    @lazy_attribute
    def ship_manager_company_code(self):
        if self.ship_manager is None:
            return None

        number = Faker('random_int', min=1000000, max=9999999).generate({})
        return str(number)

    @lazy_attribute
    def technical_manager_company_code(self):
        if self.technical_manager is None:
            return None

        number = Faker('random_int', min=1000000, max=9999999).generate({})
        return str(number)


class BulkScreeningFactory(BaseModelFactory):

    account_id = Faker('random_int')
    status = FuzzyChoice(BulkScreeningStatus)

    class Meta:
        model = BulkScreening
        sqlalchemy_session_persistence = 'flush'

    @lazy_attribute
    def imo_id(self):
        return str(Faker('random_int', max=9999999).generate({}))

    @lazy_attribute
    def result(self):
        if self.status == BulkScreeningStatus.SCHEDULED:
            return None

        return Faker('boolean').generate({})


class ScreeningResultFactory(BaseModelFactory):

    # company sanctions
    ship_registered_owner_company_severity = FuzzyChoice(Severity)
    ship_operator_company_severity = FuzzyChoice(Severity)
    ship_beneficial_owner_company_severity = FuzzyChoice(Severity)
    ship_manager_company_severity = FuzzyChoice(Severity)
    ship_technical_manager_company_severity = FuzzyChoice(Severity)
    ship_company_associates_severity = FuzzyChoice(Severity)

    ship_inspections_severity = FuzzyChoice(Severity)
    ship_association_severity = FuzzyChoice(Severity)
    ship_sanction_severity = FuzzyChoice(Severity)
    ship_flag_severity = FuzzyChoice(Severity)
    ship_registered_owner_severity = FuzzyChoice(Severity)
    ship_operator_severity = FuzzyChoice(Severity)
    ship_beneficial_owner_severity = FuzzyChoice(Severity)
    ship_manager_severity = FuzzyChoice(Severity)
    ship_technical_manager_severity = FuzzyChoice(Severity)
    doc_company_severity = FuzzyChoice(Severity)
    port_visits_severity = FuzzyChoice(Severity)
    zone_visits_severity = FuzzyChoice(Severity)


class ScreeningFactory(ScreeningResultFactory, BaseModelFactory):

    account_id = Faker('random_int')
    status = FuzzyChoice(Status)

    severity = FuzzyChoice(Severity)
    severity_change = FuzzyChoice(SeverityChange)

    ship_registered_owner_company_status = FuzzyChoice(Status)
    ship_operator_company_status = FuzzyChoice(Status)
    ship_beneficial_owner_company_status = FuzzyChoice(Status)
    ship_manager_company_status = FuzzyChoice(Status)
    ship_technical_manager_company_status = FuzzyChoice(Status)

    ship_inspections_status = FuzzyChoice(Status)
    ship_association_status = FuzzyChoice(Status)
    ship_sanction_status = FuzzyChoice(Status)
    ship_flag_status = FuzzyChoice(Status)
    ship_registered_owner_status = FuzzyChoice(Status)
    ship_operator_status = FuzzyChoice(Status)
    ship_beneficial_owner_status = FuzzyChoice(Status)
    ship_manager_status = FuzzyChoice(Status)
    ship_technical_manager_status = FuzzyChoice(Status)
    doc_company_status = FuzzyChoice(Status)
    port_visits_status = FuzzyChoice(Status)
    zone_visits_status = FuzzyChoice(Status)

    class Meta:
        model = Screening
        sqlalchemy_session_persistence = 'flush'

    @lazy_attribute
    def previous_severity(self):
        if bool(getrandbits(1)):
            return None

        return FuzzyChoice(Severity).fuzz()

    @lazy_attribute
    def previous_severity_date(self):
        if bool(getrandbits(1)):
            return None

        return Faker('date_this_decade', before_today=True).generate({})


class BaseScreeningReportFactory(BaseModelFactory):

    ship_info = Faker('ship_info_report')
    ship_registered_owner_company = Faker(
        'ship_registered_owner_company_report')
    ship_operator_company = Faker('ship_operator_company_report')
    ship_beneficial_owner_company = Faker(
        'ship_beneficial_owner_company_report')
    ship_manager_company = Faker('ship_manager_company_report')
    ship_technical_manager_company = Faker(
        'ship_technical_manager_company_report')
    ship_company_associates = Faker(
        'ship_company_associates_report')

    ship_association = Faker('ship_association_report')
    ship_sanction = Faker('ship_sanction_report')

    ship_flag = Faker('ship_flag_report')
    ship_registered_owner = Faker('ship_registered_owner_report')
    ship_operator = Faker('ship_operator_report')
    ship_beneficial_owner = Faker('ship_beneficial_owner_report')
    ship_manager = Faker('ship_manager_report')
    ship_technical_manager = Faker('ship_technical_manager_report')
    doc_company = Faker('doc_company_report')

    ship_inspections = Faker('ship_inspections_report')

    port_visits = Faker('ship_movements_report')
    zone_visits = Faker('zone_visits_report')


class ScreeningReportFactory(BaseScreeningReportFactory, BaseModelFactory):

    class Meta:
        model = ScreeningReport
        sqlalchemy_session_persistence = 'flush'


class ScreeningHistoryFactory(
        ScreeningResultFactory, BaseScreeningReportFactory, BaseModelFactory):

    severity_date = LazyFunction(lambda: datetime.now())

    class Meta:
        model = ScreeningHistory
        sqlalchemy_session_persistence = 'flush'


class ShipInspectionFactory(BaseModelFactory):

    ship_id = Faker('random_int')
    inspection_id = LazyFunction(
        lambda: str(randint(100000000000000, 999999999999999)))
    inspection_date = LazyFunction(lambda: date.today())
    authority = Faker('country')
    detained_days = Faker('pyfloat', right_digits=None)
    defects_count = Faker('random_int', max=10)
    port_name = Faker('company')
    country_name = Faker('country')

    class Meta:
        model = ShipInspection
        sqlalchemy_session_persistence = 'flush'

    @lazy_attribute
    def detained(self):
        return bool(self.detained_days)


class SISComplianceAssociationFactory(BaseModelFactory):

    class Meta:
        model = SISComplianceAssociation
        sqlalchemy_session_persistence = 'flush'


class SISCompanyFactory(BaseModelFactory):

    name = Faker('company')

    class Meta:
        model = SISCompany
        sqlalchemy_session_persistence = 'flush'

    @lazy_attribute
    def sis_code(self):
        number = Faker('random_int', min=1000000, max=9999999).generate({})
        return str(number)


class ComplianceEntityFactory(BaseModelFactory):

    entity_type = FuzzyChoice(EntityType)
    compliance_id = Faker('random_int')
    name = Faker('company')

    class Meta:
        model = ComplianceEntity
        sqlalchemy_session_persistence = 'flush'


class CompanyAssociationFactory(BaseModelFactory):

    relationship = Faker('street_name')

    class Meta:
        model = CompanyAssociation
        sqlalchemy_session_persistence = 'flush'


class ComplianceEntitySanctionFactory(BaseModelFactory):

    compliance_id = Faker('random_int')
    severity = FuzzyChoice(Severity)

    @lazy_attribute
    def start_date(self):
        if bool(getrandbits(1)):
            return None

        return Faker('date_this_decade', before_today=True).generate({})

    @lazy_attribute
    def end_date(self):
        if bool(getrandbits(1)):
            return None

        if self.start_date is None:
            return Faker('date_this_decade').generate({})

        return self.start_date + timedelta(days=randint(5, 50))

    class Meta:
        model = ComplianceEntitySanction
        sqlalchemy_session_persistence = 'flush'


class ComplianceSanctionFactory(BaseModelFactory):

    code = Faker('random_int')
    sanction_list_name = Faker('company')

    class Meta:
        model = ComplianceSanction
        sqlalchemy_session_persistence = 'flush'


class BlacklistedSanctionListFactory(BaseModelFactory):

    class Meta:
        model = BlacklistedSanctionList
        sqlalchemy_session_persistence = 'flush'


class ShipSanctionFactory(BaseModelFactory):

    ship_id = Faker('random_int')
    code = Faker('random_int')
    sanction_list_name = Faker('company')
    is_active = Faker('boolean')

    class Meta:
        model = ShipSanction
        sqlalchemy_session_persistence = 'flush'

    @lazy_attribute
    def start_date(self):
        if bool(getrandbits(1)):
            return None

        return Faker('date_this_decade', before_today=True).generate({})

    @lazy_attribute
    def end_date(self):
        if bool(getrandbits(1)):
            return None

        if self.start_date is None:
            return Faker('date_this_decade').generate({})

        return self.start_date + timedelta(days=randint(5, 50))


class Factory:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def create(cls, session: Session) -> 'Factory':
        return cls(
            create_blacklisted_country=BlacklistedCountryFactory.bind(session),
            create_blacklisted_sanction_list=BlacklistedSanctionListFactory.
            bind(session),
            create_sis_company=SISCompanyFactory.bind(session),
            create_compliance_entity=ComplianceEntityFactory.bind(session),
            create_company_association=CompanyAssociationFactory.bind(session),
            create_ship=ShipFactory.bind(session),
            create_screening=ScreeningFactory.bind(session),
            create_screenings_history=ScreeningHistoryFactory.bind(session),
            create_screening_report=ScreeningReportFactory.bind(session),
            create_bulk_screening=BulkScreeningFactory.bind(session),
            create_ship_inspection=ShipInspectionFactory.bind(session),
            create_ship_sanction=ShipSanctionFactory.bind(session),
            create_compliance_sanction=ComplianceSanctionFactory.bind(session),
            create_entity_sanction=ComplianceEntitySanctionFactory.bind(
                session),
        )
