"""Screening API blacklisted sanctions models module"""
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.types import Integer

from screening_api.models import BaseModel


class BlacklistedSanctionListItem(BaseModel):

    __tablename__ = 'blacklisted_sanctions_lists_items'

    blacklisted_sanction_list_id = Column(
        Integer,
        ForeignKey(
            'blacklisted_sanctions_lists.id',
            onupdate="CASCADE", ondelete="CASCADE",
        ),
        nullable=False, index=True,
    )
    sanction_code = Column(Integer, nullable=False)

    blacklisted_sanction_list = relationship(
        "BlacklistedSanctionList",
        backref='blacklisted_sanctions_lists_items',
    )

    __table_args__ = (
        UniqueConstraint(
            'blacklisted_sanction_list_id', 'sanction_code',
            name=(
                'blacklisted_sanction_list_id_'
                'sanction_code_unique'
            ),
        ),
    )

    @classmethod
    def creator(cls, code: int, **data: dict):
        if data is None:
            data = {}

        return cls(sanction_code=code, **data)


class BlacklistedSanctionList(BaseModel):

    __tablename__ = 'blacklisted_sanctions_lists'

    # @todo: uncomment when screening profile model implemented
    # screening_profile_id = Column(
    #     Integer,
    #     ForeignKey(
    #         'screenings_profiles.id',
    #         onupdate="CASCADE", ondelete="CASCADE",
    #     ),
    #     nullable=False,
    # )

    sanction_codes = association_proxy(
        "blacklisted_sanctions_lists_items", "sanction_code",
        creator=BlacklistedSanctionListItem.creator,
    )
