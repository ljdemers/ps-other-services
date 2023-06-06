from django.contrib.admin.helpers import Fieldline
from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from ships import models
from ships.admin.ship_inspection import ShipDefectInline


class AdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='test')
        self.user.is_staff = True
        self.user.save()
        self.user.user_permissions.add(
            *Permission.objects.filter(
                codename__startswith='change_', content_type__app_label='ships'
            )
        )
        self.client.login(username='test_user', password='test')
        self.ship = models.ShipData.objects.create(
            imo_id='1234567',
            mmsi="123456789",
            ship_name="SS ONE",
            flag_name='Denmark',
            data={
                "imo_id": "1234567",
                "attr1": "value1",
                "attr2": "value2",
                "mmsi": "123456789",
                "ship_name": "SS ONE",
                "flag_name": "Denmark",
            },
        )
        self.inspection = models.ShipInspection.objects.create(
            inspection_id="100061720110929",
            imo_id='1234567',
            authorisation="Paris MOU",
            ship_name="ATLANTIC GOOSE ",
            call_sign="V3MA",
            flag_name="Belize",
            shipclass="Lloyd's Register",
            shiptype="Other Special Activities",
            expanded_inspection="False",
            inspection_date="2011-09-29",
            date_release="2011-09-29",
            no_days_detained="0",
            port_name="Malta (Valletta)",
            country_name="Malta",
            manager="KOTA LTD.",
            detained="False",
            no_defects="2",
            source="Paris MOU",
            gt="352",
            other_inspection_type="Initial Inspection",
        )
        models.ShipDefect.objects.create(
            defect_id="67642518",
            inspection_id="100061720110929",
            defect_text="Working and Living Conditions - Working Conditions - Protection machines/parts - Not as required",
            defect_code="0820",
            recognised_org_resp_yn="N",
            main_defect_code="0800",
            main_defect_text="Working and Living Conditions",
            detention_reason_deficiency="N",
        )
        models.ShipDefect.objects.create(
            defect_id="67642519",
            inspection_id="100061720110929",
            defect_text="Fire safety - Means of escape - Not as required",
            defect_code="0960",
            recognised_org_resp_yn="N",
            main_defect_code="0900",
            main_defect_text="Fire safety",
            detention_reason_deficiency="N",
        )

    def test_view_ship(self):
        url = reverse('admin:ships_shipdata_change', args=(self.ship.pk,))

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['has_add_permission'])
        self.assertFalse(resp.context['has_delete_permission'])

        form = resp.context['adminform']
        readwrite = [
            field
            for field in form.fieldsets[0][1]['fields']
            if field not in form.readonly_fields
        ]
        (fld,) = Fieldline(
            form.form,
            'formatted_data',
            form.readonly_fields,
            model_admin=form.model_admin,
        )
        self.assertIn("<tr><td>Flag Name</td><td>Denmark</td></tr>", fld.contents())

        formsets = resp.context['inline_admin_formsets']
        self.assertEqual(len(formsets), 1)

    def test_change_ship_data(self):
        url = reverse('admin:ships_shipdata_change', args=(self.ship.pk,))
        data = {
            'mmsi': '123456789',
            'ship_name': 'SS ONE',
            'flag_name': 'Zimbabwe',
            'reason_of_change': 'Y U NO trust?',
            'shipimage_set-TOTAL_FORMS': 1,
            'shipimage_set-INITIAL_FORMS': 0,
            'shipimage_set-MIN_NUM_FORMS': 0,
            'shipimage_set-MAX_NUM_FORMS': 1000,
            'shipimage_set-__prefix__-id': '',
            'shipimage_set-__prefix__-ship_data': self.ship.pk,
            'shipimage_set-__prefix__-imo_id': '',
            'shipimage_set-__prefix__-source': '',
            'shipimage_set-__prefix__-taken_date_0': '',
            'shipimage_set-__prefix__-taken_date_1': '',
            'shipimage_set-__prefix__-url': '',
            'shipimage_set-__prefix__-filename': '',
            'shipimage_set-__prefix__-width': '',
            'shipimage_set-__prefix__-height': '',
            '_save': 'Save',
        }
        resp = self.client.post(url, data=data, follow=True)
        self.assertEqual(resp.status_code, 200)
        changed_ship = models.ShipData.objects.last()
        self.assertEqual(changed_ship.flag_name, 'Zimbabwe')
        self.assertEqual(changed_ship.data['flag_name'], 'Zimbabwe')
        change_object = models.ShipDataManualChange.objects.last()
        self.assertEqual(change_object.old_data, {'flag_name': 'Denmark'})
        self.assertEqual(change_object.new_data, {'flag_name': 'Zimbabwe'})

    def test_change_ship_mmsi(self):
        url = reverse('admin:ships_shipdata_change', args=(self.ship.pk,))
        data = {
            'mmsi': '998822001',
            'ship_name': 'SS ONE',
            'flag_name': 'Denmark',
            'reason_of_change': 'Y U NO trust?',
            'mmsi_effective_from': '12/02/2019',
            'shipimage_set-TOTAL_FORMS': 1,
            'shipimage_set-INITIAL_FORMS': 0,
            'shipimage_set-MIN_NUM_FORMS': 0,
            'shipimage_set-MAX_NUM_FORMS': 1000,
            'shipimage_set-__prefix__-id': '',
            'shipimage_set-__prefix__-ship_data': self.ship.pk,
            'shipimage_set-__prefix__-imo_id': '',
            'shipimage_set-__prefix__-source': '',
            'shipimage_set-__prefix__-taken_date_0': '',
            'shipimage_set-__prefix__-taken_date_1': '',
            'shipimage_set-__prefix__-url': '',
            'shipimage_set-__prefix__-filename': '',
            'shipimage_set-__prefix__-width': '',
            'shipimage_set-__prefix__-height': '',
            '_save': 'Save',
        }
        resp = self.client.post(url, data=data, follow=True)
        self.assertEqual(resp.status_code, 200)
        changed_ship = models.ShipData.objects.last()
        self.assertEqual(changed_ship.mmsi, '998822001')
        self.assertEqual(changed_ship.data['mmsi'], '998822001')
        change_object = models.ShipDataManualChange.objects.last()
        self.assertEqual(change_object.old_data, {'mmsi': '123456789'})
        self.assertEqual(change_object.new_data, {'mmsi': '998822001'})

    def test_change_ship_mmsi_fail(self):
        url = reverse('admin:ships_shipdata_change', args=(self.ship.pk,))
        data = {
            'mmsi': '998822001',
            'ship_name': 'SS ONE',
            'flag_name': 'Denmark',
            'reason_of_change': 'Y U NO trust?',
            'shipimage_set-TOTAL_FORMS': 1,
            'shipimage_set-INITIAL_FORMS': 0,
            'shipimage_set-MIN_NUM_FORMS': 0,
            'shipimage_set-MAX_NUM_FORMS': 1000,
            'shipimage_set-__prefix__-id': '',
            'shipimage_set-__prefix__-ship_data': self.ship.pk,
            'shipimage_set-__prefix__-imo_id': '',
            'shipimage_set-__prefix__-source': '',
            'shipimage_set-__prefix__-taken_date_0': '',
            'shipimage_set-__prefix__-taken_date_1': '',
            'shipimage_set-__prefix__-url': '',
            'shipimage_set-__prefix__-filename': '',
            'shipimage_set-__prefix__-width': '',
            'shipimage_set-__prefix__-height': '',
            '_save': 'Save',
        }
        resp = self.client.post(url, data=data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.context_data['errors'].data[0][0],
            'If you provide new MMSI you also have to provide ' 'effective from date',
        )
        changed_ship = models.ShipData.objects.last()
        self.assertEqual(changed_ship.mmsi, '123456789')
        self.assertEqual(changed_ship.data['mmsi'], '123456789')

    def test_change_ship_data_restricted_key(self):
        """If the ship object doesn't change, that's
        behaviour that we've expected"""
        url = reverse('admin:ships_shipdata_change', args=(self.ship.pk,))
        data = {
            'mmsi': '123456789',
            'ship_name': 'SS ONE',
            'flag_name': 'Denmark',
            'reason_of_change': 'Y U NO trust?',
            'data': {'sumkey': 'sumvalue'},
            'shipimage_set-TOTAL_FORMS': 1,
            'shipimage_set-INITIAL_FORMS': 0,
            'shipimage_set-MIN_NUM_FORMS': 0,
            'shipimage_set-MAX_NUM_FORMS': 1000,
            'shipimage_set-__prefix__-id': '',
            'shipimage_set-__prefix__-ship_data': self.ship.pk,
            'shipimage_set-__prefix__-imo_id': '',
            'shipimage_set-__prefix__-source': '',
            'shipimage_set-__prefix__-taken_date_0': '',
            'shipimage_set-__prefix__-taken_date_1': '',
            'shipimage_set-__prefix__-url': '',
            'shipimage_set-__prefix__-filename': '',
            'shipimage_set-__prefix__-width': '',
            'shipimage_set-__prefix__-height': '',
            '_save': 'Save',
        }
        resp = self.client.post(url, data=data, follow=True)
        self.assertEqual(resp.status_code, 200)
        changed_ship = models.ShipData.objects.last()
        self.assertEqual(changed_ship.data, self.ship.data)

    def test_change_ship_data_incorrect_data_type(self):
        """If the ship object doesn't change, that's
        behaviour that we've expected"""
        url = reverse('admin:ships_shipdata_change', args=(self.ship.pk,))
        data = {
            'mmsi': '123456789',
            'ship_name': 'SS ONE',
            'flag_name': 'Denmark',
            'gross_tonnage': "JUST TROLLIN",
            'reason_of_change': 'Y U NO trust?',
            'shipimage_set-TOTAL_FORMS': 1,
            'shipimage_set-INITIAL_FORMS': 0,
            'shipimage_set-MIN_NUM_FORMS': 0,
            'shipimage_set-MAX_NUM_FORMS': 1000,
            'shipimage_set-__prefix__-id': '',
            'shipimage_set-__prefix__-ship_data': self.ship.pk,
            'shipimage_set-__prefix__-imo_id': '',
            'shipimage_set-__prefix__-source': '',
            'shipimage_set-__prefix__-taken_date_0': '',
            'shipimage_set-__prefix__-taken_date_1': '',
            'shipimage_set-__prefix__-url': '',
            'shipimage_set-__prefix__-filename': '',
            'shipimage_set-__prefix__-width': '',
            'shipimage_set-__prefix__-height': '',
            '_save': 'Save',
        }
        resp = self.client.post(url, data=data, follow=True)
        self.assertEqual(resp.status_code, 200)
        changed_ship = models.ShipData.objects.last()
        self.assertEqual(changed_ship.data, self.ship.data)

    def test_change_ship_data_no_reason(self):
        """If the ship object doesn't change, that's
        behaviour that we've expected"""
        url = reverse('admin:ships_shipdata_change', args=(self.ship.pk,))
        data = {
            'mmsi': '123456789',
            'ship_name': 'SS ONE',
            'flag_name': 'Denmark',
            'gross_tonnage': "JUST TROLLIN",
            'shipimage_set-TOTAL_FORMS': 1,
            'shipimage_set-INITIAL_FORMS': 0,
            'shipimage_set-MIN_NUM_FORMS': 0,
            'shipimage_set-MAX_NUM_FORMS': 1000,
            'shipimage_set-__prefix__-id': '',
            'shipimage_set-__prefix__-ship_data': self.ship.pk,
            'shipimage_set-__prefix__-imo_id': '',
            'shipimage_set-__prefix__-source': '',
            'shipimage_set-__prefix__-taken_date_0': '',
            'shipimage_set-__prefix__-taken_date_1': '',
            'shipimage_set-__prefix__-url': '',
            'shipimage_set-__prefix__-filename': '',
            'shipimage_set-__prefix__-width': '',
            'shipimage_set-__prefix__-height': '',
            '_save': 'Save',
        }
        resp = self.client.post(url, data=data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.context_data['adminform'].errors['reason_of_change'][0],
            'This field is required.',
        )

    def test_view_shipinspection(self):
        url = reverse('admin:ships_shipinspection_change', args=(self.inspection.pk,))

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['has_add_permission'])
        self.assertFalse(resp.context['has_delete_permission'])

        form = resp.context['adminform']
        readwrite = [
            field
            for field in form.fieldsets[0][1]['fields']
            if field not in form.readonly_fields
        ]
        self.assertEqual(readwrite, [], "All fields should be marked readonly")
        formsets = resp.context['inline_admin_formsets']
        self.assertEqual(len(formsets), 1)
        self.assertIsInstance(formsets[0].opts, ShipDefectInline)
        self.assertEqual(len(formsets[0].formset.forms), 2)
