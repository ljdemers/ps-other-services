from enum import Enum
from typing import Text

from django.core.management import BaseCommand, CommandParser

from ships.utils import log_execution


class BaseHistoryCommand(BaseCommand):
    log_file_prefix: Text = ...
    batch_size: int = 100

    class Action(Enum):
        POPULATE = 'populate'
        IGNORE = 'ignore'

    def add_arguments(self, parser: CommandParser):
        subparsers = parser.add_subparsers(
            title="action",
            dest="action",
        )
        subparsers.required = True

        subparsers.add_parser(
            self.Action.POPULATE.value, help='Populate historical data.'
        )

        ignore_parser = subparsers.add_parser(
            self.Action.IGNORE.value,
            help='Find and ignore duplicates in existing records.',
        )
        ignore_parser.add_argument(
            '--exclude-manual',
            action='store_true',
            required=False,
            default=False,
            help='Exclude manually created records.',
        )

    def handle(self, *args, **options):
        action = self.Action(options['action'])
        exclude_manual = options.get('exclude_manual', False)
        is_history_populated = False

        with log_execution(self.log_file_prefix):
            if action is self.Action.POPULATE:
                is_history_populated = self.populate_history()

            if action is self.Action.IGNORE:
                is_history_populated = True
                self.clean_ignored_records(exclude_manual)

            if is_history_populated:
                self.mark_ignored_records(exclude_manual)

    def populate_history(self):
        raise NotImplementedError

    def clean_ignored_records(self, exclude_manual: bool = False):
        raise NotImplementedError

    def mark_ignored_records(self, exclude_manual: bool = False):
        raise NotImplementedError
