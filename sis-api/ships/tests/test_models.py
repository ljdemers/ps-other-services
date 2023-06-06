# -*- coding: utf8 -*-
from __future__ import unicode_literals
from datetime import timedelta

from copy import deepcopy
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from ships.models import (
    MMSIHistory,
    ShipData,
    ShipMovement
)


class TestShipMovementManager(TestCase):

    def setUp(self):
        self.attrs = {
            'ArrivalDate': '2014-09-04',
            'ArrivalDateFull': '2014-09-04 10:37:53',
            'Country': 'France',
            'CallID': '53796943',
            'DateCreated': '2014-09-04 15:13:19.960000000',
            'Destination': 'Antibes',
            'ETA':  '9999-12-31 23:59:59',
            'HoursinPort': '1',
            'LRNOIMOShipNo': '1000021',
            'LastPortofCallArrivalDate': '',
            'LastPortofCallCode': '1361',
            'LastPortofCallCountry': 'Kuwait',
            'LastPortofCallCountryCode': 'KWT',
            'LastPortofCallName': 'Shuwaikh',
            'LastPortofCallSailDate': '2015-09-29T11:32:41.824585+00:00',
            'Movementtype': None,
            'PortLatitudeDecimal': '43.56187438999999999',
            'PortLongitudeDecimal': '101.01268824555555555',

            'Port': 'Cannes',
            'PortGeoID': 'ihs_port_geo_id',
            'PortID': 'ihs_port_id',
            'SailDate': '2014-09-04',
            'SailDateFull': '2014-09-04 11:55:53',
            'ShipName': 'MONTKAJ',
            'ShipType': 'Yacht',

             # Should deleted by import_data and be set automatically by ORM
            'creation_date': '2014-09-04 10:37:53',
        }

        self.bad_attrs = {
            'LastPortofCallName': 'Shuwaikh',
            'LastPortofCallSailDate': '2015-09-29T11:32:41.824585+00:00',
            'movement_type': None,
            'PortLatitudeDecimal': '93.56187438999999999',
            'PortLongitudeDecimal': '181.01268824555555555',
        }

        self.bad_attrs2 = {
            'LastPortofCallName': 'Port Hello',
            'LastPortofCallSailDate': '2015-09-29T11:32:41.824585+00:00',
            'movement_type': None,
            'PortLatitudeDecimal': '-93.56187438999999999',
            'PortLongitudeDecimal': '-181.01268824555555555',
        }

    def test_ship_movement_import_data(self):
        ship_movement = ShipMovement.objects.import_data(self.attrs)

        self.assertEqual(ship_movement.longitude, Decimal('101.012688'))

        self.assertEqual(ship_movement.latitude, Decimal('43.561874'))

        now = timezone.now()
        self.assertEqual(ship_movement.creation_date.year, now.year)
        self.assertEqual(ship_movement.creation_date.month, now.month)
        self.assertEqual(ship_movement.creation_date.day, now.day)

        self.assertIsNone(ship_movement.last_port_of_call_arrival_date)

    def test_ship_movement_import_data_with_bad_data(self):
        ship_movement = ShipMovement.objects.import_data(self.bad_attrs)

        self.assertIsNone(ship_movement.latitude)
        self.assertIsNone(ship_movement.longitude)
        self.assertEqual(ship_movement.last_port_of_call_name, 'Shuwaikh')

        ship_movement = ShipMovement.objects.import_data(self.bad_attrs2)

        self.assertIsNone(ship_movement.latitude)
        self.assertIsNone(ship_movement.longitude)
        self.assertEqual(ship_movement.last_port_of_call_name, 'Port Hello')


class TestShipData(TestCase):
    """Test cases for `ShipData` to be stored properly when new data
     is imported"""

    def setUp(self):
        self.attrs = {
            'call_sign': 'BSEY',
            'data': 'null',
            'flag_name': u"China, People's Republic Of",
            'gross_tonnage': 2878.0,
            'group_beneficial_owner': 'China National Offshore Oil',
            'imo_id': '9744283',
            'mmsi': '444444444',
            'length_overall_loa': 66.799999999999997,
            'operator': 'China Oilfield Services Ltd',
            'port_of_registry': 'Tianjin',
            'registered_owner': 'China Oilfield Services Ltd',
            'ship_manager': 'China Oilfield Services Ltd',
            'ship_name': 'HAI YANG SHI YOU 751',
            'ship_status': 'In Service/Commission',
            'shiptype_level_5': 'Research Survey Vessel',
            'technical_manager': 'Unknown',
            'updated': '2017-07-11T12:38:53Z',
        }
        MMSIHistory.objects.all().delete()
        self.data = {'call_sign': 'BSEY',}
        # creating a dummy MMSIHistory data
        MMSIHistory.objects.create(
            mmsi='222222222',
            imo_number=self.attrs['imo_id'],
            effective_from=timezone.now() - timedelta(days=90),
            effective_to=timezone.now() - timedelta(days=60),
        )

        MMSIHistory.objects.create(
            mmsi='333333333',
            imo_number=self.attrs['imo_id'],
            effective_from=timezone.now() - timedelta(days=60),
            effective_to=timezone.now() - timedelta(days=30),
        )

        MMSIHistory.objects.create(
            mmsi='444444444',
            imo_number=self.attrs['imo_id'],
            effective_from=timezone.now() - timedelta(days=30)
        )

        # creating a dummy ship data
        self.ship_data_pk = 100
        ShipData.objects.create(
            pk=self.ship_data_pk, **self.attrs)

    def tearDown(self):
        MMSIHistory.objects.all().delete()
        ShipData.objects.all().delete()

    def test_importing_data_creates_mmsi_history(self):
        """Test creation of `MMSIHistory` record when data is imported"""
        ship_data_pk = ShipData.objects.import_data(
            attrs=deepcopy(self.attrs),
            data=self.data)

        self.assertEqual(ship_data_pk, 100)

        latest_mmsi = MMSIHistory.objects.filter(
            imo_number=self.attrs['imo_id'],
            mmsi=self.attrs['mmsi']
        )

        self.assertEqual(latest_mmsi.count(), 1)

        mmsi_history = MMSIHistory.objects.filter(
            imo_number=self.attrs['imo_id'])

        self.assertEqual(mmsi_history.count(), 3)

        ship_data = ShipData.objects.get(pk=ship_data_pk)

        self.assertEqual(self.attrs['mmsi'], latest_mmsi[0].mmsi)
        self.assertEqual(ship_data.mmsi, latest_mmsi[0].mmsi)

    def test_importing_data_creates_mmsi_history_and_adds_effective_to(self):
        """Test replacement of `MMSIHistory` record with a new one"""
        mmsi_histories = MMSIHistory.objects.filter(
            imo_number=self.attrs['imo_id'],
        )
        self.assertEqual(mmsi_histories.count(), 3)

        self.assertEqual(MMSIHistory.objects.filter(
            imo_number=self.attrs['imo_id'],
            effective_to__isnull=True
        ).count(), 1)

        mmsi_history1 = MMSIHistory.objects.filter(
            imo_number=self.attrs['imo_id'],
            effective_to__isnull=True
        )[0]
        self.assertEqual('444444444', mmsi_history1.mmsi)

    def test_importing_data_creates_new_mmsi_history(self):
        attrs = deepcopy(self.attrs)
        mmsi = '999999999'
        attrs['mmsi'] = mmsi
        ship_data_pk = ShipData.objects.import_data(
            attrs=attrs,
            data=self.data)

        self.assertEqual(
            ShipData.objects.get(pk=ship_data_pk).mmsi, mmsi)

        mmsi_histories = MMSIHistory.objects.filter(
            imo_number=self.attrs['imo_id'],
        )

        self.assertEqual(mmsi_histories.count(), 4)

        histories = MMSIHistory.objects.filter(
            imo_number=self.attrs['imo_id'],
            effective_to__isnull=True)

        self.assertEqual(histories.count(), 1)
        self.assertEqual(histories[0].mmsi, mmsi)

        ship_data = ShipData.objects.get(pk=ship_data_pk)

        self.assertEqual(ship_data.mmsi, mmsi)


class TestMMSIHistory(TestCase):
    """Test cases for `MMSIHistory` replacement scenarions (PTRAC-4499)"""

    def setUp(self):
        MMSIHistory.objects.all().delete()

        some_mmsi = self.mmsi = '999999999'

        self.attrs = {
            'call_sign': 'BSEY',
            'data': {},
            'flag_name': u"China, People's Republic Of",
            'gross_tonnage': 2878.0,
            'group_beneficial_owner': 'China National Offshore Oil',
            'imo_id': '9744283',
            'length_overall_loa': 66.799999999999997,
            'operator': 'China Oilfield Services Ltd',
            'port_of_registry': 'Tianjin',
            'registered_owner': 'China Oilfield Services Ltd',
            'ship_manager': 'China Oilfield Services Ltd',
            'ship_name': 'HAI YANG SHI YOU 751',
            'ship_status': 'In Service/Commission',
            'shiptype_level_5': 'Research Survey Vessel',
            'technical_manager': 'Unknown',
            'updated': '2017-07-11T12:38:53Z',
        }
        self.data = {'call_sign': 'BSEY',}

        # creating a dummy MMSIHistory data
        MMSIHistory.objects.create(
            mmsi=111111111,
            imo_number=self.attrs['imo_id'],
            effective_from=timezone.now() - timedelta(days=90),
            effective_to=timezone.now() - timedelta(days=60),
        )

        MMSIHistory.objects.create(
            mmsi=222222222,
            imo_number=self.attrs['imo_id'],
            effective_from=timezone.now() - timedelta(days=60),
            effective_to=timezone.now() - timedelta(days=30),
        )

        MMSIHistory.objects.create(
            mmsi=333333333,
            imo_number=self.attrs['imo_id'],
            effective_from=timezone.now() - timedelta(days=30),
            effective_to=timezone.now() - timedelta(days=15),
        )

        MMSIHistory.objects.create(
            mmsi=some_mmsi,
            imo_number=self.attrs['imo_id'],
            effective_from=timezone.now() - timedelta(days=15),
        )

        # creating a dummy ship data
        self.ship_data_pk = 100
        ShipData.objects.create(
            pk=self.ship_data_pk, mmsi=some_mmsi, **self.attrs)

    def tearDown(self):
        MMSIHistory.objects.all().delete()
        ShipData.objects.all().delete()

    def test_importing_data_store_proper_mmsi_history_no_changes(self):
        """Pass an MMSI equal to the one currently in `ShipData`"""

        attrs = {
            'call_sign': 'BSEY',
            'data': {},
            'flag_name': u"China, People's Republic Of",
            'gross_tonnage': 2878.0,
            'group_beneficial_owner': 'China National Offshore Oil',
            'imo_id': '9744283',
            'length_overall_loa': 66.799999999999997,
            'mmsi': self.mmsi,  # mmsi not changing from store ship data
            'operator': 'China Oilfield Services Ltd',
            'port_of_registry': 'Tianjin',
            'registered_owner': 'China Oilfield Services Ltd',
            'ship_manager': 'China Oilfield Services Ltd',
            'ship_name': 'HAI YANG SHI YOU 751',
            'ship_status': 'In Service/Commission',
            'shiptype_level_5': 'Research Survey Vessel',
            'technical_manager': 'Unknown',
            'updated': '2017-07-11T12:38:53Z',
        }

        # update IHS data
        ShipData.objects.import_data(
            attrs=deepcopy(attrs),
            data=self.data)

        # check current ship data
        ship_data = ShipData.objects.get(pk=self.ship_data_pk)

        self.assertEqual(ship_data.mmsi, self.mmsi)

        self.assertEqual(MMSIHistory.objects.filter(
            mmsi=attrs['mmsi'],
            imo_number=attrs['imo_id'],
            effective_to__isnull=True).count(), 1)

    def test_importing_data_store_proper_mmsi_history_stale_mmsi(self):
        """Pass an MMSI that is already in MMSIHistory"""
        attrs = {
            'call_sign': 'BSEY',
            'data': {},
            'flag_name': u"China, People's Republic Of",
            'gross_tonnage': 2878.0,
            'group_beneficial_owner': 'China National Offshore Oil',
            'imo_id': '9744283',
            'length_overall_loa': 66.799999999999997,
            'mmsi': 222222222,
            'operator': 'China Oilfield Services Ltd',
            'port_of_registry': 'Tianjin',
            'registered_owner': 'China Oilfield Services Ltd',
            'ship_manager': 'China Oilfield Services Ltd',
            'ship_name': 'HAI YANG SHI YOU 751',
            'ship_status': 'In Service/Commission',
            'shiptype_level_5': 'Research Survey Vessel',
            'technical_manager': 'Unknown',
            'updated': '2017-07-11T12:38:53Z',
        }

        # update IHS data
        ShipData.objects.import_data(attrs=attrs, data=self.data)

        # check current ship data
        ship_data = ShipData.objects.get(pk=self.ship_data_pk)

        # stored MMSI should be equal to the one already stored, not the one in
        # attributes
        self.assertEqual(
            ship_data.mmsi,
            MMSIHistory.objects.filter(
                imo_number=attrs['imo_id'],
                effective_to__isnull=True
            )[0].mmsi)

        self.assertEqual(MMSIHistory.objects.filter(
            imo_number=attrs['imo_id'],
            effective_to__isnull=True).count(), 1)

    def test_importing_data_store_proper_mmsi_history_new_mmsi(self):
        """Pass a brand new MMSI"""
        attrs = {
            'call_sign': 'BSEY',
            'data': {},
            'flag_name': u"China, People's Republic Of",
            'gross_tonnage': 2878.0,
            'group_beneficial_owner': 'China National Offshore Oil',
            'imo_id': '9744283',
            'length_overall_loa': 66.799999999999997,
            'mmsi': '000000000',
            'operator': 'China Oilfield Services Ltd',
            'port_of_registry': 'Tianjin',
            'registered_owner': 'China Oilfield Services Ltd',
            'ship_manager': 'China Oilfield Services Ltd',
            'ship_name': 'HAI YANG SHI YOU 751',
            'ship_status': 'In Service/Commission',
            'shiptype_level_5': 'Research Survey Vessel',
            'technical_manager': 'Unknown',
            'updated': '2017-07-11T12:38:53Z',
        }

        ship_data_pk = ShipData.objects.import_data(
            attrs=deepcopy(attrs),
            data=self.data)

        ship_data = ShipData.objects.get(pk=ship_data_pk)

        self.assertEqual(ship_data.mmsi, '000000000')

        self.assertEqual(MMSIHistory.objects.filter(
             imo_number=attrs['imo_id'],
             effective_to__isnull=True).count(), 1)

    def test_importing_data_store_proper_mmsi_history_empty_mmsi(self):
        """Pass a brand new MMSI"""
        attrs = {
            'call_sign': 'BSEY',
            'data': {},
            'flag_name': u"China, People's Republic Of",
            'gross_tonnage': 2878.0,
            'group_beneficial_owner': 'China National Offshore Oil',
            'imo_id': '9744283',
            'length_overall_loa': 66.799999999999997,
            'mmsi': None,
            'operator': 'China Oilfield Services Ltd',
            'port_of_registry': 'Tianjin',
            'registered_owner': 'China Oilfield Services Ltd',
            'ship_manager': 'China Oilfield Services Ltd',
            'ship_name': 'HAI YANG SHI YOU 751',
            'ship_status': 'In Service/Commission',
            'shiptype_level_5': 'Research Survey Vessel',
            'technical_manager': 'Unknown',
            'updated': '2017-07-11T12:38:53Z',
        }

        ship_data_pk = ShipData.objects.import_data(
            attrs=deepcopy(attrs),
            data=self.data)

        ship_data = ShipData.objects.get(pk=ship_data_pk)
        self.assertEqual(ship_data.mmsi, None)
        closed_histies_count = MMSIHistory.objects.filter(
            imo_number=attrs['imo_id'],
            effective_to__isnull=True).count()
        self.assertEqual(closed_histies_count, 0)
