"""Screening API blacklisted countries models module"""
from sqlalchemy.schema import Column
from sqlalchemy.types import String, Enum

from screening_api.models import BaseModel
from screening_api.screenings.enums import Severity


class BlacklistedCountry(BaseModel):

    __tablename__ = 'blacklisted_countries'

    # @todo: uncomment when screening profile model implemented
    # screening_profile_id = Column(
    #     Integer,
    #     ForeignKey(
    #         'screenings_profiles.id',
    #         onupdate="CASCADE", ondelete="CASCADE",
    #     ),
    #     nullable=False,
    # )
    # @todo: remove unique when screening profile model implemented
    country_id = Column(String, nullable=False, unique=True)
    # @todo: remove unique when screening profile model implemented
    country_name = Column(String, nullable=False, unique=True)
    severity = Column(
        Enum(Severity), default=Severity.UNKNOWN,
        nullable=False,
    )
