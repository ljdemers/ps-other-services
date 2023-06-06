from screening_api.company_associations.repositories import (
    CompanyAssociationsRepository,
)
from screening_api.sanctions.repositories import (
    ComplianceEntitySanctionsRepository,
)
from screening_api.ship_sanctions.repositories import (
    ShipSanctionsRepository,
)

from screening_workers.lib.api.cache.collections import BaseCachedCollection
from screening_workers.lib.compliance_api.cache.updaters import (
    ShipSanctionsUpdater, CompanySanctionsUpdater,
)


class ShipSanctionsCollection(BaseCachedCollection):

    def __init__(
            self,
            ship_sanctions_repository: ShipSanctionsRepository,
            ship_sanctions_updater: ShipSanctionsUpdater,
    ):
        self.ship_sanctions_repository = ship_sanctions_repository
        self.ship_sanctions_updater = ship_sanctions_updater

    def invalidate(self, ship_id):
        return self.ship_sanctions_repository.delete(ship_id=ship_id)

    def refresh(self, ship_id):
        return self.ship_sanctions_updater.update(ship_id)

    def query(self, ship_id, blacklisted_sanction_list_id=None):
        self.refresh(ship_id)
        # always use cache
        return self.ship_sanctions_repository.find(
            ship_id=ship_id,
            blacklisted_sanction_list_id=blacklisted_sanction_list_id,
        )


class CompanySanctionsCollection(BaseCachedCollection):

    def __init__(
            self,
            sanctions_repository: ComplianceEntitySanctionsRepository,
            company_sanctions_updater: CompanySanctionsUpdater,
    ):
        self.sanctions_repository = sanctions_repository
        self.company_sanctions_updater = company_sanctions_updater

    def invalidate(self, ship_id):
        # @todo: remove related
        return self.sanctions_repository.delete(ship_id=ship_id)

    def refresh(self, company_id):
        return self.company_sanctions_updater.update(company_id)

    def query(
            self, ship_id, associate_type, blacklisted_sanction_list_id=None):
        # always use cache
        return self.sanctions_repository.find_sanctions(
            ship_id, associate_type,
            blacklisted_sanction_list_id=blacklisted_sanction_list_id,
            joinedload_related=['compliance_sanction'],
            sort=['id', ],
        )


class CompanyAssociationsCollection(BaseCachedCollection):

    def __init__(
            self,
            company_associations_repository: CompanyAssociationsRepository,
            company_sanctions_updater: CompanySanctionsUpdater,
    ):
        self.company_associations_repository = company_associations_repository
        self.company_sanctions_updater = company_sanctions_updater

    def invalidate(self, company_id):
        # @todo: remove related
        return self.company_associations_repository.delete(
            entity_id=company_id)

    def refresh(self, company_ids):
        return list(map(self.company_sanctions_updater.update, company_ids))

    def query(self, company_ids):
        self.refresh(company_ids)
        # always use cache
        return self.company_associations_repository.find_all_associations(
            company_ids,
            joinedload_related=['dst.entity_sanctions', ],
            subqueryload=['compliance_sanction', ],
        )
