from django.db.models import Q

from ships.management.base_history import BaseHistoryCommand
from ships.models import FlagHistory
from ships.utils.flag_history import (get_flag_history, get_ship_history,
                                      mark_ignored_history_records,
                                      populate_flag_history)


class Command(BaseHistoryCommand):
    log_file_prefix = 'flag_history'
    help = 'Populates FlagHistory data from ShipDataHistory.'

    def populate_history(self):
        ship_history = get_ship_history()
        flag_history_ids = populate_flag_history(ship_history)

        return flag_history_ids

    def clean_ignored_records(self, exclude_manual: bool = False):
        history_filters = Q(ignore=True)
        if exclude_manual:
            history_filters &= Q(manual_edit=False)

        FlagHistory.objects.filter(history_filters).update(ignore=False)

    def mark_ignored_records(self, exclude_manual: bool = False):
        flag_history = get_flag_history(exclude_manual)
        mark_ignored_history_records(flag_history)
