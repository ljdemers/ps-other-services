from django.core.management.base import BaseCommand
from django.db.models.query import RawQuerySet
from ships.models import MMSIHistory, ShipData


class Command(BaseCommand):
    """
    https://jira.polestarglobal.com/browse/PTRAC-5394

    - Find out entries in the MMSI history table where a ship has more than one MMSI active right now.
    - If found, go to the affected ships and work out the old MMSIs that have no 'effective to' dates.
        - The one with the latest Effective from date is the valid one.
    - For the old MMSIs with no 'effective to' dates, work out what those dates would be by looking at their MMSI successors' Effective from dates. Update the data.

    https://pole-star-global.monday.com/boards/865892212/pulses/1216972195

    We need to write a management command that corrects any duplicate mmsi
    history records with no effective_to dates.

    The shipdata record has the current correct MMSI.

    * If the newer record's MMSI does not match shipdata then log and continue
    * If the MMSIs have the same effective from date then log and continue
    * If the duplicate MMSI's are in order, then set the older record's effective_to date as the effective_from date of the newer record and log
    * have a dry run command to output all the problematic ships
    """

    help = 'Correct duplicate MMSI history records with no effective_to dates.'

    initial_query = """
    SELECT b.id, b.imo_number, mmsi, effective_from, effective_to
    FROM ships_mmsihistory b
    JOIN (
        SELECT imo_number, count(*)
        FROM ships_mmsihistory
        WHERE effective_to IS NULL
        GROUP BY 1
        HAVING count(*) > 1
    ) a
    ON a.imo_number = b.imo_number
    ORDER BY b.imo_number, effective_from DESC;
    """

    def load_mmsi_history(self) -> RawQuerySet:
        return MMSIHistory.objects.raw(self.initial_query)

    def correct_mmsi_history(self, mmsi_history: RawQuerySet, do_commit: bool = False):
        prev = None
        updated_mmsi_ids = []

        self.stdout.write('imo_number,mmsi_hist_id,effective_from,original_effective_to,updated_effective_to,')
        for row in mmsi_history:
            if getattr(prev, 'imo_number', None) == row.imo_number:
                log_str = ','.join(map(str, (row.imo_number, row.id, row.effective_from, row.effective_to)))
                if not prev.effective_from:
                    self.stdout.write(f'{log_str},,')
                else:
                    self.stdout.write(f'{log_str},{prev.effective_from},')
                    if do_commit:
                        row.effective_to = prev.effective_from
                        row.save()
                    updated_mmsi_ids.append(row.id)
            prev = row

        self.stderr.write(
            self.style.NOTICE(f'Updated MMSI Records: {updated_mmsi_ids}')
        )

    def add_arguments(self, parser):
        parser.add_argument(
            '--commit',
            action='store_true',
            required=False,
            default=False,
            help=(
                'Commit changes to the database. Without this flag the script does a DRY-RUN.'
            ),
        )

    def handle(self, *args, **options):
        do_commit = bool(options['commit'])

        if not do_commit:
            self.stderr.write(self.style.NOTICE('DRY-RUN - no data is being modified.'))

        mmsi_history_data = self.load_mmsi_history()
        self.correct_mmsi_history(mmsi_history_data, do_commit)

        if not do_commit:
            self.stderr.write(self.style.NOTICE('DRY-RUN - no data was modified.'))
