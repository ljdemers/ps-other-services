import itertools
import logging
from operator import itemgetter

from django.core.management.base import BaseCommand

from ships.models import CompanyHistory
from ships.models.company_history import CompanyAssociationTypes
from ships.utils import get_first, log_execution
from ships.utils.company_history import UNKNOWN_COMPANY_CODE

logger = logging.getLogger('management')

BATCH_SIZE = 100


class Command(BaseCommand):
    help = 'Fix companyhistory effective_date values.'

    @log_execution('companyhistory_effective_date')
    def handle(self, *args, **options):
        # we want to consider only records that were previously blank
        imo_ids = (
            CompanyHistory.objects.filter(company_code=UNKNOWN_COMPANY_CODE)
            .distinct()
            .values_list('imo_id', flat=True)
        )
        imo_ids_iter = imo_ids.iterator()

        count = 0
        total_count = imo_ids.count()

        logger.info('%s IMOs with unknown companies found...', total_count)
        while True:
            selected_imo_ids = list(itertools.islice(imo_ids_iter, BATCH_SIZE))
            if not selected_imo_ids:
                break

            for association_type in CompanyAssociationTypes:
                company_history = (
                    CompanyHistory.objects.filter(
                        imo_id__in=selected_imo_ids,
                        association_type=association_type.value,
                        manual_edit=False,
                    )
                    .order_by('imo_id', 'timestamp')  # earliest first
                    .values('id', 'timestamp', 'imo_id', 'company_code')
                )

                # find the correct effective_date
                # and set it for the rest records in the group
                for _, group in itertools.groupby(
                    company_history, itemgetter('imo_id', 'company_code')
                ):
                    companies = list(group)
                    # first company contains the earliest timestamp
                    # because of the ordering we did in the query above
                    effective_date = get_first(companies)['timestamp']

                    CompanyHistory.objects.filter(
                        id__in=[company['id'] for company in companies]
                    ).update(effective_date=effective_date)

            count += len(selected_imo_ids)
            logger.info('%s/%s IMOs done', count, total_count)
