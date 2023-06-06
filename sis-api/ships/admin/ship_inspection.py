import logging

from django.contrib import admin
from django.db import models
from django.forms.widgets import TextInput

from ships.models import ShipDefect, ShipInspection

log = logging.getLogger(__name__)


class ShipDefectInline(admin.TabularInline):
    """
    Inline table view of ship defects imported from IHS/SeaWeb.
    """

    model = ShipDefect
    formfield_overrides = {models.TextField: {"widget": TextInput}}
    extra = 0
    fields = (  # 'defect_id',
        "defect_code",
        "defect_text",
        "main_defect_code",
        "main_defect_text",
        ("action_1", "action_code_1"),
        ("action_2", "action_code_2"),
        ("action_3", "action_code_3"),
        "other_action",
        "recognised_org_resp_yn",
        "recognised_org_resp_code",
        "recognised_org_resp",
        "other_recognised_org_resp",
        "class_is_responsible",
        "detention_reason_deficiency",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


class ShipInspectionAdmin(admin.ModelAdmin):
    """
    Admin screen to view ship inspections imported from IHS/Fairplay.
    """

    inlines = [ShipDefectInline]
    list_display = (
        "inspection_id",
        "imo_id",
        "ship_name",
        "inspection_date",
        "port_name",
        "country_name",
        "no_defects",
        "detained",
    )
    list_filter = ("detained",)
    search_fields = ("imo_id",)

    fieldsets = (
        (None, {"fields": ("inspection_id", "imo_id", "ship_name")}),
        (
            "Ship information",
            {
                "fields": (
                    "call_sign",
                    "flag_name",
                    "shipclass",
                    "shiptype",
                    "owner",
                    "manager",
                    "charterer",
                    "cargo",
                    "gt",
                    "dwt",
                    "yob",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Port", {"fields": ("port_name", "country_name")}),
        (
            "Inspection",
            {
                "fields": (
                    "authorisation",
                    "inspection_date",
                    "date_release",
                    "detained",
                    "no_days_detained",
                    "number_part_days_detained",
                    "expanded_inspection",
                    "other_inspection_type",
                    "source",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


admin.site.register(ShipInspection, ShipInspectionAdmin)
