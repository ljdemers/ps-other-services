import logging

from django.contrib import admin

from ships.models import MMSIHistory

log = logging.getLogger(__name__)


class MMSIHistoryAdmin(admin.ModelAdmin):

    search_fields = (
        "imo_number",
        "mmsi",
    )

    list_display = ("id", "imo_number", "mmsi", "effective_to", "effective_from")

    list_filter = ("effective_to",)
    fields = (
        "imo_number",
        "mmsi",
        "effective_from",
        "effective_to",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ["imo_number", "mmsi", "effective_from", "formatted_data"]


admin.site.register(MMSIHistory, MMSIHistoryAdmin)
