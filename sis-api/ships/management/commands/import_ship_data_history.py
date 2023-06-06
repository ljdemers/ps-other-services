from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ships.utils import convert_file_timestamp, get_first, time_it
from ships.utils.ship_history import import_ship_data_history


class Command(BaseCommand):
    help = 'Imports data from files into ShipDataHistory model\'s table.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            action='store',
            required=False,
            default='/opt/data',
            type=str,
            help=(
                'A path to a directory that contains CSV files to import data '
                'from into a model.'
            ),
        )
        parser.add_argument(
            '--file-mask',
            action='store',
            required=False,
            default='*ShipData.CSV',
            type=str,
            help='A pattern of characters used to match file names.',
        )
        parser.add_argument(
            '--batch-size',
            action='store',
            required=False,
            default=100,
            type=int,
            help=(
                'A parameter to control how many objects are created in a '
                'single query.'
            ),
        )

    @time_it
    def handle(self, *args, **options):
        path = Path(options['path']).resolve()
        if not path.exists():
            raise CommandError(f'There is no such path {path}')

        files = list(path.rglob(options['file_mask']))
        if not files:
            raise CommandError(
                'No files were matched against such pattern: ' f'{options["file_mask"]}'
            )

        for posix_path in files:
            with posix_path.open(mode='r', encoding='utf-8') as file_obj:
                timestamp = convert_file_timestamp(
                    get_first(posix_path.name.split('_'))
                )
                import_ship_data_history(file_obj, timestamp, options['batch_size'])

        self.stdout.write(self.style.SUCCESS('Data imported successfully.'))
