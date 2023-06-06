import logging

from django.contrib import admin

from ships.models import FlagHistory

log = logging.getLogger(__name__)


class FlagHistoryAdmin(admin.ModelAdmin):
    search_fields = (
        "imo_id",
        "flag_name",
    )

    list_display = (
        "timestamp",
        "imo_id",
        "flag_name",
        "flag_effective_date",
        "manual_edit",
        "ignore",
    )

    def source_flag_effective_date(self, obj):
        return getattr(obj.ship_history, "flag_effective_date", None)

    source_flag_effective_date.short_description = "Source flag effective date"

    def get_readonly_fields(self, request, obj=None):
        fields = ("ship_history", "manual_edit")
        if obj and obj.ship_history:  # editing the generated object
            fields += (
                "imo_id",
                "flag_name",
                "flag_effective_date",
                "source_flag_effective_date",
                "timestamp",
                "flag",
            )

        return fields

    def get_fieldsets(self, request, obj=None):
        flag_fields = (
            "flag_name",
            "flag",
            "flag_effective_date",
        )
        if obj and obj.ship_history:
            flag_fields += ("source_flag_effective_date",)

        return (
            (
                None,
                {
                    "fields": (
                        "timestamp",
                        "imo_id",
                        "ship_history",
                    )
                },
            ),
            (
                "Flag data",
                {"fields": flag_fields},
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


admin.site.register(FlagHistory, FlagHistoryAdmin)
