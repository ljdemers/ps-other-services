"""Screening API screenings models module"""
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Column, ForeignKey, Index
from sqlalchemy.types import Integer, Enum, DateTime

from screening_api.models import BaseModel
from screening_api.screenings.enums import Severity, SeverityChange, Status


class ScreeningResult:

    # company sanctions
    ship_registered_owner_company_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    ship_operator_company_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    ship_beneficial_owner_company_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    ship_manager_company_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    ship_technical_manager_company_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    ship_company_associates_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )

    # ship inspections
    ship_inspections_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )

    # ship sanctions
    ship_association_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    ship_sanction_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )

    # country sanctions
    ship_flag_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    ship_registered_owner_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    ship_operator_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    ship_beneficial_owner_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    ship_manager_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    ship_technical_manager_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    doc_company_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )  # Document of Compliance

    # ship movements
    port_visits_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
    zone_visits_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )

    @property
    def ship_sanctions_severity(self):
        return self.calculated_ship_sanctions_severity

    @property
    def calculated_ship_sanctions_severity(self):
        return max([
            self.ship_association_severity, self.ship_sanction_severity,
        ])

    @property
    def company_sanctions_severity(self):
        return self.calculated_company_sanctions_severity

    @property
    def calculated_company_sanctions_severity(self):
        return max([
            self.ship_registered_owner_company_severity,
            self.ship_operator_company_severity,
            self.ship_beneficial_owner_company_severity,
            self.ship_manager_company_severity,
            self.ship_technical_manager_company_severity,
            self.ship_company_associates_severity,
        ])

    @property
    def country_sanctions_severity(self):
        return self.calculated_country_sanctions_severity

    @property
    def calculated_country_sanctions_severity(self):
        return max([
            self.ship_flag_severity, self.ship_registered_owner_severity,
            self.ship_operator_severity, self.ship_beneficial_owner_severity,
            self.ship_manager_severity, self.ship_technical_manager_severity,
            self.doc_company_severity,
        ])

    @property
    def ship_movements_severity(self):
        return self.calculated_ship_movements_severity

    @property
    def calculated_ship_movements_severity(self):
        return max([self.port_visits_severity, self.zone_visits_severity])

    @property
    def calculated_severity(self):
        return self.get_calculated_severity()

    def get_calculated_severity(self):
        return max([
            self.company_sanctions_severity, self.ship_sanctions_severity,
            self.country_sanctions_severity, self.ship_inspections_severity,
            self.ship_movements_severity,
        ])


class ScreeningStatus:

    # company sanctions
    ship_registered_owner_company_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    ship_operator_company_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    ship_beneficial_owner_company_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    ship_manager_company_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    ship_technical_manager_company_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    ship_company_associates_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )

    # ship sanctions
    ship_association_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    ship_sanction_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )

    # country sanctions
    ship_flag_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    ship_registered_owner_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    ship_operator_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    ship_beneficial_owner_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    ship_manager_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    ship_technical_manager_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    doc_company_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )  # Document of Compliance

    # ship inspections
    ship_inspections_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )

    # ship movements
    port_visits_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )
    zone_visits_status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )

    status = Column(
        Enum(Status), default=Status.CREATED,
        nullable=False,
    )

    @property
    def ship_sanctions_status(self):
        return max([
            self.ship_association_status, self.ship_sanction_status,
        ])

    @property
    def company_sanctions_status(self):
        return max([
            self.ship_registered_owner_company_status,
            self.ship_operator_company_status,
            self.ship_beneficial_owner_company_status,
            self.ship_manager_company_status,
            self.ship_technical_manager_company_status,
            self.ship_company_associates_status,
        ])

    @property
    def country_sanctions_status(self):
        return max([
            self.ship_flag_status, self.ship_registered_owner_status,
            self.ship_operator_status, self.ship_beneficial_owner_status,
            self.ship_manager_status, self.ship_technical_manager_status,
            self.doc_company_status,
        ])

    @property
    def ship_movements_status(self):
        return max([self.port_visits_status, self.zone_visits_status])

    @property
    def calculated_status(self):
        return self.get_calculated_status()

    def get_calculated_status(self):
        return max([
            self.company_sanctions_status, self.ship_sanctions_status,
            self.country_sanctions_status, self.ship_inspections_status,
            self.ship_movements_status,
        ])


class Screening(ScreeningResult, ScreeningStatus, BaseModel):

    __tablename__ = 'screenings'

    ship_id = Column(
        Integer,
        ForeignKey('ships.id', onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    account_id = Column(Integer, index=True)

    company_sanctions_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False, index=True,
    )
    ship_sanctions_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False, index=True,
    )
    country_sanctions_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False, index=True,
    )
    ship_movements_severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False, index=True,
    )

    severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False, index=True,
    )
    severity_change = Column(
        Enum(SeverityChange), default=SeverityChange.NOCHANGE,
        nullable=False, index=True,
    )
    previous_severity = Column(Enum(Severity), nullable=True)
    previous_severity_date = Column(DateTime, nullable=True)

    ship = relationship(
        "Ship",
        backref=backref("screenings", cascade="all, delete-orphan"),
    )

    __table_args__ = (
        Index('ix_screenings_created', 'created'),
        Index(
            'ix_screenings_ship_inspections_severity',
            'ship_inspections_severity',
        ),
    )

    def __json__(self):
        return [
            'id', 'created', 'updated', 'ship_id', 'account_id', 'severity',
            'severity_change', 'ship', 'status', 'previous_severity',
            'previous_severity_date',
        ]

    @property
    def result(self):
        """Combined status, severity and severity_change property"""
        if not self.status == Status.DONE:
            return self.status.name

        if self.severity_change == SeverityChange.INCREASED:
            return ' '.join([self.severity.name, 'ESCALATED'])

        return self.severity.name

    @property
    def calculated_severity_change(self):
        return self.get_calculated_severity_change()

    def get_calculated_severity_change(self):
        if self.previous_severity is None:
            return SeverityChange.NOCHANGE

        if Severity.UNKNOWN in [self.previous_severity, self.severity]:
            return SeverityChange.NOCHANGE

        if self.previous_severity > self.severity:
            return SeverityChange.DECREASED

        if self.previous_severity < self.severity:
            return SeverityChange.INCREASED

        return SeverityChange.NOCHANGE
