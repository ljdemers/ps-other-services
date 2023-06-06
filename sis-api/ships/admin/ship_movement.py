import logging

from django.contrib import admin
from django.core.paginator import Paginator
from django.db import OperationalError, connection, transaction
from django.utils.functional import cached_property

from ships.models import ShipMovement

log = logging.getLogger(__name__)


class TimeLimitedPaginator(Paginator):
    """
    Paginator that enforces a timeout on the count operation.
    If the operations times out, a fake bogus value is
    returned instead.
    """

    @cached_property
    def count(self):
        # We set the timeout in a db transaction to prevent it from
        # affecting other transactions.
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout TO 200;")
            try:
                return super().count
            except OperationalError:
                return 9999999999


class ShipMovementAdmin(admin.ModelAdmin):
    paginator = TimeLimitedPaginator
    show_full_result_count = False

    list_display = (
        "imo_id",
        "timestamp",
        "ihs_id",
    )


admin.site.register(ShipMovement, ShipMovementAdmin)
