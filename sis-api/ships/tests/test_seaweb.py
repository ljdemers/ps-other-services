from django.test import TestCase

from ships import seaweb


class TestSeawebUtils(TestCase):

    def test_translate_underscored(self):
        self.assertEqual(seaweb.translate('dAte_of_BuilD'), 'date_of_build')  # just lowercase it

    def test_translate_capwords(self):
        self.assertEqual(seaweb.translate('CallSign'), 'call_sign')

    def test_translate_acronyms(self):
        self.assertEqual(seaweb.translate('IMOChemicalClassIII'), 'imo_chemical_class_iii')

    def test_translate_of(self):
        self.assertEqual(seaweb.translate('DateofBuild'), 'date_of_build')

    def test_translate_to(self):
        self.assertEqual(seaweb.translate('BowtoCentreManifold'), 'bow_to_centre_manifold')

    def test_translate_in(self):
        self.assertEqual(seaweb.translate('HeatingCoilsinTanks'), 'heating_coils_in_tanks')

    def test_translate_number(self):
        self.assertEqual(seaweb.translate('FuelType1Code'), 'fuel_type_1_code')

    def test_translate_unit(self):
        self.assertEqual(seaweb.translate('FlashPointOver60c'), 'flash_point_over_60c')