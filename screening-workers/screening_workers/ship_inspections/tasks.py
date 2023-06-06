from screening_workers.lib.screening.tasks import CheckTask


class ShipInspectionsCheckTask(CheckTask):

    name = 'screening.ship_inspections.ship_inspections_check'
