"""Screening API screenings reports validators module"""
from jsonschema import RefResolver, validate


class ReportSchemaValidator:

    def __init__(self, schema, spec_path):
        self.schema = schema
        self.spec_path = spec_path

    @property
    def resolver(self):
        return RefResolver('file://{0}'.format(self.spec_path), None)

    def validate(self, data):
        validate(data, self.schema, resolver=self.resolver)
