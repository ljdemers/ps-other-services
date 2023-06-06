import itertools
import logging
from typing import List, Union

from django.core.management import color_style
from django.db.models import Q, QuerySet

from ships import models
from ships.management.base_history import BaseHistoryCommand
from ships.models.company_history import (CompanyAssociationTypes,
                                          CompanyHistory)
from ships.utils.company_history import (get_company_history, get_ship_history,
                                         mark_ignored_history_records,
                                         populate_company_history)

style = color_style()
logger = logging.getLogger('management')


class Command(BaseHistoryCommand):
    log_file_prefix = 'company_history'
    help = 'Populates CompanyHistory data from ShipDataHistory.'

    def populate_history(self):
        logger.info('Populating company history...')

        imo_ids = self._get_imo_ids()
        imo_ids_iter = imo_ids.iterator()

        count = 0
        total_count = imo_ids.count()

        num_created = 0
        while True:
            selected_imo_ids = list(itertools.islice(imo_ids_iter, self.batch_size))
            if not selected_imo_ids:
                break

            ship_history = self._get_ship_history(selected_imo_ids)
            for association_type in CompanyAssociationTypes:
                company_ids = populate_company_history(association_type, ship_history)
                num_created += len(company_ids)

            count += len(selected_imo_ids)
            logger.info('%s/%s IMOs done', count, total_count)

        logger.info(
            style.SUCCESS('%s company history records created successfully.'),
            num_created,
        ) if num_created else logger.error(
            style.ERROR('No company history records created.')
        )

        return num_created

    def clean_ignored_records(self, exclude_manual: bool = False):
        history_filters = Q(ignore=True)
        if exclude_manual:
            history_filters &= Q(manual_edit=False)

        CompanyHistory.objects.filter(history_filters).update(ignore=False)

    def mark_ignored_records(self, exclude_manual: bool = False):
        total_ignored = 0
        for association_type in CompanyAssociationTypes:
            company_history = get_company_history(association_type, exclude_manual)
            num_ignored = mark_ignored_history_records(company_history)

            total_ignored += num_ignored

        logger.warning(
            style.WARNING('%s company history records marked as ignored.'),
            total_ignored,
        )

    @staticmethod
    def _get_imo_ids() -> Union[QuerySet, List[models.ShipDataHistory]]:
        """List all ships' IMOs.

        Returns:
            queryset: ship history.
        """
        return models.ShipDataHistory.objects.distinct('imo_id').values_list(
            'imo_id', flat=True
        )

    @staticmethod
    def _get_ship_history(
        imo_ids: List,
    ) -> Union[QuerySet, List[models.ShipDataHistory]]:
        """Retrieve ship history for specific IMOs.

        Args:
            imo_ids (list): IMO IDs to get ship history for.

        Returns:
            queryset: ship history.
        """
        ship_history = get_ship_history()
        ship_history = ship_history.filter(imo_id__in=imo_ids)

        return ship_history
