from screening_workers.lib.screening.tasks import CheckTask


class ShipMovementsCheckTask(CheckTask):

    name = 'screening.ship_movements.port_visits_check'


class ZoneVisitsCheckTask(CheckTask):

    name = 'screening.ship_movements.zone_visits_check'
