import logging

from django.contrib import admin

from ships.models import CompanyHistory

log = logging.getLogger(__name__)


class CompanyHistoryAdmin(admin.ModelAdmin):
    search_fields = ("imo_id", "company_code", "company_name")
    list_display = (
        "timestamp",
        "effective_date",
        "imo_id",
        "company_code",
        "company_name",
        "get_association_type",
        "manual_edit",
        "ignore",
    )

    def get_association_type(self, obj):
        return obj.association_type

    get_association_type.short_description = "Association type"
    get_association_type.admin_order_field = 'association_type'

    def get_readonly_fields(self, request, obj=None):
        fields = ("ship_history", "manual_edit")
        if obj and obj.ship_history:  # editing the generated object
            fields += (
                "timestamp",
                "imo_id",
                "get_association_type",
                "company_name",
                "company_code",
                "company_registration_country",
                "company_control_country",
                "company_domicile_country",
                "company_domicile_code",
            )

        return fields

    def get_fieldsets(self, request, obj=None):
        return (
            (
                None,
                {
                    "fields": (
                        "timestamp",
                        "effective_date",
                        "imo_id",
                        "ship_history",
                    )
                },
            ),
            (
                "Company data",
                {
                    "fields": (
                        "company_code",
                        "get_association_type"
                        if obj and obj.ship_history
                        else "association_type",
                        "company_registration_country",
                        "company_name",
                        "company_control_country",
                        "company_domicile_country",
                        "company_domicile_code",
                    )
                },
            ),
            (
                "Additional info",
                {
                    "fields": (
                        "ignore",
                        "manual_edit",
                    )
                },
            ),
        )

    def save_model(self, request, obj, form, change):
        if not obj.ship_history:
            obj.manual_edit = True

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return not obj or obj.manual_edit


admin.site.register(CompanyHistory, CompanyHistoryAdmin)
