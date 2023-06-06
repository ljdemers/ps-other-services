import logging

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from ships.models import ShipDataManualChange

log = logging.getLogger(__name__)


class ShipDataManualChangeAdmin(admin.ModelAdmin):
    """
    Admin page for the changes of shipdata model
    """

    fields = [
        "changed_ship",
        "user",
        "date_of_change",
        "old_data",
        "new_data",
        "link_to_user",
        "link_to_ship",
        "reason",
    ]
    readonly_fields = ["link_to_user", "link_to_ship", "expired"]

    list_display = ["changed_ship", "user", "date_of_change"]
    search_fields = (
        "changed_ship__ship_name",
        "user__username",
        "changed_ship__imo_id",
    )

    def link_to_user(self, obj):
        link = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}">The user profile url {}</a>', link, obj.user)

    link_to_user.short_description = "See the user"
    link_to_user.allow_tags = True

    def link_to_ship(self, obj):
        link = reverse("admin:ships_shipdata_change", args=[obj.changed_ship.id])
        return format_html(
            '<a href="{}">The ship data url {}</a>', link, obj.changed_ship
        )

    link_to_ship.short_description = "See the ship data"
    link_to_ship.allow_tags = True

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields] + self.readonly_fields


admin.site.register(ShipDataManualChange, ShipDataManualChangeAdmin)
