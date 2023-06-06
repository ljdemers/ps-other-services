from screening_workers.lib.api.collections import Collection
from screening_workers.lib.sis_api.models import Ship, ShipInspection, \
    IhsMovement


class InspectionsCollection(Collection):
    model = ShipInspection
    url = 'inspections/'

    def decode(self, raw, many=False):
        if many:
            raw = raw['objects']
        return super(InspectionsCollection, self).decode(raw, many=many)


class IhsMovementCollection(Collection):
    model = IhsMovement
    url = 'ship_movement/'

    def decode(self, raw, many=False):
        if many:
            raw = raw['objects']
        return super(IhsMovementCollection, self).decode(raw, many=many)


class ShipsCollection(Collection):
    model = Ship
    url = 'ships/'

    def decode(self, raw, many=False):
        if many:
            raw = raw['objects']
        return super(ShipsCollection, self).decode(raw, many=many)


class ShipInspectionsCollection(Collection):
    model = ShipInspection
    url = 'ships/{0}/inspections/'

    def decode(self, raw, many=False):
        if many:
            raw = raw['objects']
        return super(ShipInspectionsCollection, self).decode(raw, many=many)

    def all(self, ship_id):
        url = self.url.format(ship_id)
        response = self.client.fetch(url)

        response.raise_for_status()

        data = response.json()

        return self.decode(data, many=True)
