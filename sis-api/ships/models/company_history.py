import logging
from enum import Enum

from django.db import models
from django.db.models import fields

logger = logging.getLogger(__name__)


class CompanyAssociationTypes(Enum):
    REGISTERED_OWNER = "Registered Owner"
    OPERATOR = "Operator"
    SHIP_MANAGER = "Ship Manager"
    TECHNICAL_MANAGER = "Technical Manager"
    GROUP_BENEFICIAL_OWNER = "Group Beneficial Owner"

    @classmethod
    def choices(cls):
        return (
            (cls.REGISTERED_OWNER.name, cls.REGISTERED_OWNER.value),
            (cls.OPERATOR.name, cls.OPERATOR.value),
            (cls.SHIP_MANAGER.name, cls.SHIP_MANAGER.value),
            (cls.TECHNICAL_MANAGER.name, cls.TECHNICAL_MANAGER.value),
            (cls.GROUP_BENEFICIAL_OWNER.name, cls.GROUP_BENEFICIAL_OWNER.value),
        )


class CompanyHistory(models.Model):
    class Meta:
        verbose_name = "company_history"
        verbose_name_plural = "company history"

    timestamp = fields.DateTimeField()
    effective_date = fields.DateTimeField()
    imo_id = fields.CharField(max_length=10, db_index=True)

    association_type = models.CharField(
        "Association type",
        max_length=30,
        choices=CompanyAssociationTypes.choices(),
        db_index=True,
        null=True,
        blank=True,
    )

    company_name = fields.CharField(
        max_length=255, db_index=True, null=True, blank=True
    )
    company_code = fields.IntegerField(db_index=True, null=True, blank=True)
    company_registration_country = fields.CharField(
        max_length=255, null=True, blank=True
    )
    company_control_country = fields.CharField(max_length=255, null=True, blank=True)
    company_domicile_country = fields.CharField(max_length=255, null=True, blank=True)
    company_domicile_code = fields.CharField(max_length=3, null=True, blank=True)

    manual_edit = models.BooleanField(default=False)
    ignore = models.BooleanField(default=False, db_index=True)

    ship_history = models.ForeignKey(
        to="ShipDataHistory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="company_history",
    )
