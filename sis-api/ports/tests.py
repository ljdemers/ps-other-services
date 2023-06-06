from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from ports.models import Port, Country


class ModelTest(TestCase):
    def setUp(self):
        c = Country.objects.create(name='Republic of Polestar', code='RPS')
        c2 = Country.objects.create(name='Kingdom of Polestar', code='KPS')
        c.alternate_names.create(name='Polestar')
        p = Port.objects.create(name='Compass House', code='RPSCH', country=c)
        p.alternate_names.create(name='Compass', country=c)
        p.alternate_names.create(name='Compass House', country=c2)

    def test_lookup_country_code(self):
        self.assertRaises(ObjectDoesNotExist, Country.lookup, code='XYZ')
        self.assertIsInstance(Country.lookup(code='RPS'), Country)
        self.assertIsInstance(Country.lookup(code='rps'), Country, "Lookup should be case insensitive")

    def test_lookup_country_name(self):
        self.assertRaises(ObjectDoesNotExist, Country.lookup, name='Foobar')
        self.assertRaises(ObjectDoesNotExist, Country.lookup, name='of Polestar')

        self.assertIsInstance(Country.lookup(name='Polestar'), Country)
        self.assertEqual(Country.lookup(name='Polestar').code, "RPS")
        self.assertEqual(Country.lookup(name='Republic of Polestar').code, "RPS")
        self.assertEqual(Country.lookup(name='polestar').code, "RPS")
        self.assertEqual(Country.lookup(name='republic of polestar').code, "RPS")

        self.assertEqual(Country.lookup(name='kingdom of polestar').code, "KPS")

    def test_lookup_port_code(self):
        self.assertRaises(ObjectDoesNotExist, Port.lookup, code='XYZZY')
        self.assertIsInstance(Port.lookup(code='RPSCH'), Port)
        self.assertIsInstance(Port.lookup(code='rpsch'), Port, "Lookup should be case insensitive")

    def test_lookup_port_name(self):
        self.assertRaises(ObjectDoesNotExist, Port.lookup, name='Foobar', country='Polestar')
        self.assertRaises(ObjectDoesNotExist, Port.lookup, name='Compass House', country='Foobar')
        self.assertRaises(ObjectDoesNotExist, Port.lookup, name='of Polestar', country='Polestar')
        self.assertRaises(ObjectDoesNotExist, Port.lookup, name='compass', country='Kingdom of Polestar')

        self.assertIsInstance(Port.lookup(name='Compass House', country='Republic of Polestar'), Port)

        self.assertEqual(Port.lookup(name='Compass House', country='Polestar').code, 'RPSCH')
        self.assertEqual(Port.lookup(name='Compass', country='Polestar').code, 'RPSCH')
        self.assertEqual(Port.lookup(name='compass house', country='Polestar').code, 'RPSCH')
        self.assertEqual(Port.lookup(name='compass house', country='Kingdom of Polestar').code, 'RPSCH')


