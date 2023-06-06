from django.contrib import admin

from ships.models import LoadStatus


class LoadStatusAdmin(admin.ModelAdmin):
    list_display = ("filename", "started_date", "finished_date", "status")


admin.site.register(LoadStatus, LoadStatusAdmin)
