from collections import namedtuple


BaseHealth = namedtuple(
    'BaseHealth',
    ['service_type', 'status', 'notes', 'errors'],
)


class Health(BaseHealth):

    def __json__(self):
        return {
            'service_type': self.service_type,
            'status': self.status,
            'notes': self.notes,
            'errors': self.errors,
        }
