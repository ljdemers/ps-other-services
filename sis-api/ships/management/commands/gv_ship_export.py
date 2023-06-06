from django.core.management.base import BaseCommand

from ships.export import export_file_for_globavista


class Command(BaseCommand):
    help = "Create a dump of shipdata for globavista"

    def handle(self, target_filename, *args, **kwargs):
        export_file_for_globavista(
            target_filename=target_filename,
            lzma_compressed=kwargs['lzma_compressed']
        )

    def add_arguments(self, parser):
        parser.add_argument(
            'target_filename',
            type=str,
            help='Path to output file'
        )
        parser.add_argument(
            'lzma_compressed',
            type=bool,
            default=False,
            help=(
                'Whether to lzma compress the output '
                '(filename will be appended with .xz)'
            )
        )
