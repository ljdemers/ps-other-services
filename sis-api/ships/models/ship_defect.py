import logging

from django.db import models
from django.db.models import fields

from ships.models.managers.ship_defect import ShipDefectManager

logger = logging.getLogger(__name__)


class ShipDefect(models.Model):

    objects = ShipDefectManager()

    defect_id = fields.IntegerField(primary_key=True)
    inspection = models.ForeignKey(
        "ShipInspection", related_name="defects", on_delete=models.CASCADE
    )
    defect_text = models.TextField(blank=True, null=True)
    defect_code = fields.CharField(max_length=10, null=True, blank=True)
    action_1 = fields.CharField(max_length=50, null=True, blank=True)
    action_2 = fields.CharField(max_length=50, null=True, blank=True)
    action_3 = fields.CharField(max_length=50, null=True, blank=True)
    other_action = models.TextField(blank=True, null=True)
    recognised_org_resp_yn = fields.CharField(max_length=10, null=True, blank=True)
    recognised_org_resp_code = fields.CharField(max_length=10, null=True, blank=True)
    recognised_org_resp = fields.CharField(max_length=50, null=True, blank=True)
    other_recognised_org_resp = fields.CharField(max_length=10, null=True, blank=True)
    main_defect_code = fields.CharField(max_length=10, null=True, blank=True)
    main_defect_text = models.TextField(blank=True, null=True)
    action_code_1 = fields.CharField(max_length=10, null=True, blank=True)
    action_code_2 = fields.CharField(max_length=10, null=True, blank=True)
    action_code_3 = fields.CharField(max_length=10, null=True, blank=True)
    class_is_responsible = fields.CharField(max_length=10, null=True, blank=True)
    detention_reason_deficiency = fields.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return ""
