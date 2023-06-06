from screening_workers.lib.screening.tasks import CheckTask


class ShipInfoCheckTask(CheckTask):

    name = 'screening.ship_movements.ship_info_check'
