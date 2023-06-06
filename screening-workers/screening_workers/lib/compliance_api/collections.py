from screening_workers.lib.api.collections import Collection
from screening_workers.lib.compliance_api.models import Ship, OrganisationName


class ShipsCollection(Collection):
    model = Ship
    url = 'ships/'

    def decode(self, raw, many=False):
        if many:
            raw = raw['results']
        return super(ShipsCollection, self).decode(raw, many=many)


class OrganisationNamesCollection(Collection):
    model = OrganisationName
    url = 'organisation_names/'

    def decode(self, raw, many=False):
        if many:
            raw = raw['results']
        return super(OrganisationNamesCollection, self).decode(raw, many=many)
