import csv
import os
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ships.models import ShipData


class Command(BaseCommand):
    help = 'Generate CSVs ready for Compliance.'

    def add_arguments(self, parser):
        parser.add_argument(
            'sanction_name', action='store', help='Watchlist name.'
        )
        parser.add_argument(
            'path', action='store', help='Path to initial CSV with IMOs.'
        )

    def handle(self, *args, **options):
        path = Path(options['path']).resolve()
        if not os.path.exists(path):
            raise CommandError(f'There is no such path {path}')

        sanction_name = options['sanction_name']
        ships = []
        sanctions = []
        with path.open(mode='r', encoding='utf-8') as file_obj:
            for row in csv.DictReader(file_obj, delimiter=';'):
                imo_number = row['IMO/LR/IHS No.'].strip()
                try:
                    data = ShipData.objects.get(imo_id=imo_number)
                    ships.append(
                        (
                            imo_number,
                            data.ship_name,
                            data.ship_status,
                            {'International Maritime Organization (IMO) Ship No.': imo_number},
                            '',
                            {'www.purpletrac.com'},
                        )
                    )
                    sanctions.append(
                        (
                            sanction_name,
                            'Current',
                            datetime(2022, 10, 7).strftime('%Y-%m-%d'),
                            None,
                            imo_number,
                        )
                    )
                except ShipData.DoesNotExist:
                    self.stdout.write(f'Ship data with {imo_number} IMO not found.')

        ship_data_path = Path(path.parent) / f'{path.stem}_ship_data.csv'
        with ship_data_path.open(mode='w+', encoding='utf-8') as ship_data_file:
            writer = csv.writer(ship_data_file)
            writer.writerow(
                ('imo_number', 'name', 'status', 'data', 'profile_notes', 'sources')
            )
            writer.writerows(ships)
        self.stdout.write(f'{len(ships)} ships written into {ship_data_path}')

        sanctions_path = Path(path.parent) / f'{path.stem}_sanctions.csv'
        with sanctions_path.open(mode='w+', encoding='utf-8') as sanctions_file:
            writer = csv.writer(sanctions_file)
            writer.writerow(('name', 'status', 'since_date', 'to_date', 'imo_number'))
            writer.writerows(sanctions)
        self.stdout.write(f'{len(sanctions)} sanctions written into {sanctions_path}')
