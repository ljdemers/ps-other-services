import logging

from django.contrib import admin

from ships.models import LoadHistory

log = logging.getLogger(__name__)


class LoadHistoryAdmin(admin.ModelAdmin):
    list_display = ("started_date", "finished_date", "status")


admin.site.register(LoadHistory, LoadHistoryAdmin)
