from booby import Model, fields

from screening_workers.lib.utils import str2date


class Entity(Model):

    id = fields.Integer()
    name = fields.String()
    status = fields.String()

    def __repr__(self):
        return f'Entity {self.id}'

    @classmethod
    def parse(cls, raw):
        return {
            'id': raw['id'],
            'name': raw['name'],
            'status': raw['status'],
        }


class Sanction(Model):

    code = fields.Integer()
    name = fields.String()
    status = fields.String()
    severity = fields.String()

    def __repr__(self):
        return f'Sanction {self.code}'

    @classmethod
    def parse(cls, raw):
        return {
            'code': raw['code'],
            'name': raw['name'],
            'status': raw['status'],
        }


class EntitySanction(Model):

    id = fields.Integer()
    status = fields.String()
    since_date = fields.String()
    to_date = fields.String()
    sanction = fields.Embedded(Sanction)

    def __repr__(self):
        return f'EntitySanction {self.id}'

    @classmethod
    def parse(cls, raw):
        sanction = Sanction.parse(raw['sanction'])

        since_date = raw.get('since_date')
        if since_date is not None:
            since_date = str2date(since_date)

        to_date = raw.get('to_date')
        if to_date is not None:
            to_date = str2date(to_date)

        return {
            'id': raw['id'],
            'sanction': sanction,
            'status': raw['status'],
            'since_date': since_date,
            'to_date': to_date,
        }


class Ship(Entity):

    ship_sanctions = fields.Collection(EntitySanction)

    def __repr__(self):
        return f'Ship {self.id}'

    @classmethod
    def parse(cls, raw):
        ship_sanctions = list(map(
            EntitySanction.parse, raw['ship_sanctions']))

        return {
            'id': raw['id'],
            'name': raw['name'],
            'status': raw['status'],
            'ship_sanctions': ship_sanctions,
        }


class ShipEntity(Entity):

    sanctions = fields.Collection(EntitySanction)

    def __repr__(self):
        return f'ShipEntity {self.id}'

    @classmethod
    def parse(cls, raw):
        sanctions = list(map(
            EntitySanction.parse, raw.get('ship_sanctions', [])))
        entity = Entity.parse(raw)
        entity['sanctions'] = sanctions
        return entity


class OrganisationEntity(Entity):

    sanctions = fields.Collection(EntitySanction)

    def __repr__(self):
        return f'OrganisationEntity {self.id}'

    @classmethod
    def parse(cls, raw):
        sanctions = list(map(
            EntitySanction.parse, raw.get('organisation_sanctions', [])))
        entity = Entity.parse(raw)
        entity['sanctions'] = sanctions
        return entity


class PersonEntity(Entity):

    sanctions = fields.Collection(EntitySanction)

    def __repr__(self):
        return f'PersonEntity {self.id}'

    @classmethod
    def parse(cls, raw):
        sanctions = list(map(
            EntitySanction.parse, raw.get('person_sanctions', [])))
        entity = Entity.parse(raw)
        entity['sanctions'] = sanctions
        return entity


class EntityAssociation(Model):

    id = fields.Integer()
    status = fields.String()
    relationship = fields.String()
    ship = fields.Embedded(ShipEntity)
    organisation = fields.Embedded(OrganisationEntity)
    person = fields.Embedded(PersonEntity)
    parent = fields.Integer()

    def __repr__(self):
        return f'EntityAssociation {self.id}'

    @property
    def entity_type(self):
        if self.ship is not None:
            return 'ship'
        if self.organisation is not None:
            return 'organisation'
        if self.person is not None:
            return 'person'
        raise ValueError("Unknown entity type")

    @property
    def entity(self):
        return getattr(self, self.entity_type)

    @classmethod
    def parse(cls, raw):
        ship = raw.get('ship') and ShipEntity.parse(raw['ship'])
        organisation = raw.get('organisation') and OrganisationEntity.parse(
            raw['organisation'])
        person = raw.get('person') and PersonEntity.parse(raw['person'])
        return {
            'id': raw['id'],
            'status': raw['status'],
            'relationship': raw['relationship'],
            'ship': ship,
            'organisation': organisation,
            'person': person,
        }


class Organisation(Entity):

    sanctions = fields.Collection(EntitySanction)
    associations = fields.Collection(EntityAssociation)

    def __repr__(self):
        return f'Organisation {self.id}'

    @classmethod
    def parse(cls, raw):
        sanctions = list(map(
            EntitySanction.parse, raw.get('organisation_sanctions', [])))
        associations = list(map(
            EntityAssociation.parse, raw.get('organisation_associations', [])))

        entity = OrganisationEntity.parse(raw)
        entity['sanctions'] = sanctions
        entity['associations'] = associations
        return entity


class OrganisationName(Model):

    id = fields.Integer()
    name = fields.String()
    name_type = fields.String()
    organisation = fields.Embedded(Organisation)

    def __repr__(self):
        return f'OrganisationName {self.id}'

    @classmethod
    def parse(cls, raw):
        organisation = Organisation.parse(raw['organisation'])

        return {
            'id': raw['id'],
            'name': raw['name'],
            'name_type': raw['name_type'],
            'organisation': organisation,
        }
