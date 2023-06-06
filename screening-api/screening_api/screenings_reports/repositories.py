"""Screening API screenings reports repositories module"""
from datetime import datetime

from sqlalchemy.orm.scoping import scoped_session

from screening_api.lib.alchemy.queries import ExtendedQuery
from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.screenings_reports.models import ScreeningReport
from screening_api.screenings_reports.validators import (
    ReportSchemaValidator,
)


class ScreeningsReportsRepository(AlchemyRepository):

    model = ScreeningReport

    def __init__(
            self,
            session_factory: scoped_session,
            ship_info_validator: ReportSchemaValidator,
            ship_inspections_validator: ReportSchemaValidator,
            ship_sanction_validator: ReportSchemaValidator,
            ship_flag_validator: ReportSchemaValidator,
            ship_associated_country_validator: ReportSchemaValidator,
            ship_movements_validator: ReportSchemaValidator,
    ):
        super(ScreeningsReportsRepository, self).__init__(session_factory)
        self.ship_info_validator = ship_info_validator
        self.ship_inspections_validator = ship_inspections_validator
        self.ship_sanction_validator = ship_sanction_validator
        self.ship_flag_validator = ship_flag_validator
        self.ship_associated_country_validator =\
            ship_associated_country_validator
        self.ship_movements_validator = ship_movements_validator

    def create(
            self, screening_id: int,
            ship_info: dict = None,
            ship_inspections: dict = None,
            ship_sanction: dict = None,
            ship_flag: dict = None,
            ship_registered_owner: dict = None,
            ship_operator: dict = None,
            ship_beneficial_owner: dict = None,
            ship_manager: dict = None,
            ship_technical_manager: dict = None,
            ship_movements: dict = None,
            created: datetime = None, updated: datetime = None,
            **options) -> ScreeningReport:
        if ship_info is None:
            ship_info = {}

        if ship_inspections is None:
            ship_inspections = {}

        if ship_sanction is None:
            ship_sanction = {}

        if ship_flag is None:
            ship_flag = {}

        if ship_registered_owner is None:
            ship_registered_owner = {}

        if ship_operator is None:
            ship_operator = {}

        if ship_beneficial_owner is None:
            ship_beneficial_owner = {}

        if ship_manager is None:
            ship_manager = {}

        if ship_technical_manager is None:
            ship_technical_manager = {}

        if ship_movements is None:
            ship_movements = {}

        self.ship_info_validator.validate(ship_info)
        self.ship_inspections_validator.validate(ship_inspections)
        self.ship_sanction_validator.validate(ship_sanction)
        self.ship_flag_validator.validate(ship_flag)
        self.ship_associated_country_validator.validate(ship_registered_owner)
        self.ship_associated_country_validator.validate(ship_operator)
        self.ship_associated_country_validator.validate(ship_beneficial_owner)
        self.ship_associated_country_validator.validate(ship_manager)
        self.ship_associated_country_validator.validate(ship_technical_manager)
        self.ship_movements_validator.validate(ship_movements)

        data = {
            'screening_id': screening_id,
            'ship_info': ship_info,
            'ship_inspections': ship_inspections,
            'ship_sanction': ship_sanction,
            'ship_flag': ship_flag,
            'ship_registered_owner': ship_registered_owner,
            'ship_operator': ship_operator,
            'ship_beneficial_owner': ship_beneficial_owner,
            'ship_manager': ship_manager,
            'ship_technical_manager': ship_technical_manager,
            'port_visits': ship_movements,
        }

        if created:
            data['created'] = created

        if updated:
            data['updated'] = updated

        return super(ScreeningsReportsRepository, self).create(
            **data, **options)

    def update(self, id_: int, **kwargs):
        ship_info = kwargs.get('ship_info')
        if ship_info:
            self.ship_info_validator.validate(ship_info)

        ship_inspections = kwargs.get('ship_inspections')
        if ship_inspections:
            self.ship_inspections_validator.validate(ship_inspections)

        ship_sanction = kwargs.get('ship_sanction')
        if ship_sanction:
            self.ship_sanction_validator.validate(ship_sanction)

        ship_flag = kwargs.get('ship_flag')
        if ship_flag:
            self.ship_flag_validator.validate(ship_flag)

        ship_registered_owner = kwargs.get('ship_registered_owner')
        if ship_registered_owner:
            self.ship_associated_country_validator.validate(
                ship_registered_owner)

        ship_operator = kwargs.get('ship_operator')
        if ship_operator:
            self.ship_associated_country_validator.validate(ship_operator)

        ship_beneficial_owner = kwargs.get('ship_beneficial_owner')
        if ship_beneficial_owner:
            self.ship_associated_country_validator.validate(
                ship_beneficial_owner)

        ship_manager = kwargs.get('ship_manager')
        if ship_manager:
            self.ship_associated_country_validator.validate(ship_manager)

        ship_technical_manager = kwargs.get('ship_technical_manager')
        if ship_technical_manager:
            self.ship_associated_country_validator.validate(
                ship_technical_manager)

        ship_movements = kwargs.get('ship_movements')
        if ship_movements:
            self.ship_movements_validator.validate(ship_movements)

        return super(ScreeningsReportsRepository, self).update(id_, **kwargs)

    def _filter_query(self, **kwargs) -> ExtendedQuery:
        screening__account_id = kwargs.pop('screening__account_id', None)

        query = super(ScreeningsReportsRepository, self)._filter_query(
            **kwargs)

        if screening__account_id is not None:
            screening_model = self.get_rel_model('screening')
            query = query.join(screening_model).filter(
                screening_model.account_id == screening__account_id,
            )

        return query
