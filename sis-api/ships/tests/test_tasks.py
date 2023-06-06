import os
import shutil
import uuid
from io import StringIO
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from paramiko.sftp_attr import SFTPAttributes

from ships.connectors import FTPConnector
from ships.models import (Flag, LoadHistory, LoadStatus, ShipData,
                          ShipDataManualChange, ShipDefect, ShipInspection,
                          ShipMovement)
from ships.tasks import synchronise_files
from ships.tasks.ship_info import apply_manual_changes_on_ship_data
from ships.tests.factories import ShipDataFactory, ShipDataManualChangeFactory
from ships.utils.file import import_file


class ImportFileTests(TestCase):

    shipdata = '''"LRIMOShipNo","ShipName","ShipStatus","MaritimeMobileServiceIdentityMMSINumber","CallSign","FlagName","FlagEffectiveDate","PortofRegistry","OfficialNumber","ClassificationSociety","ShiptypeLevel5","StatCode5","Deadweight","GrossTonnage","NetTonnage","PanamaCanalNetTonnagePCNT","SuezCanalNetTonnageSCNT","LengthOverallLOA","LengthBetweenPerpendicularsLBP","LengthRegistered","Breadth","BreadthExtreme","BreadthMoulded","Depth","Displacement","Draught","GroupBeneficialOwner","RegisteredOwner","Operator","ShipManager","TechnicalManager","BaleCapacity","GasCapacity","GrainCapacity","IMOChemicalClassI","IMOChemicalClassII","IMOChemicalClassIII","InsulatedCapacity","LiquidCapacity","NumberofCabins","NumberofCargoPumps","NumberofCars","NumberofHatches","NumberofHolds","NumberofRamps","NumberofROROLanes","NumberofRORORamps","NumberofTanks","TEU","TEUCapacity14tHomogenous","SegregatedBallastTanks","SegregatedBallastCapacity","NumberofDecks","Shipbuilder","YearOfBuild","CountryOfBuild","KeelLaidDate","YardNumber","Speed","BareboatCharterCompany","BareboatCharterEffectiveDate","BareboatCharterCountryofControl","BareboatCharterCountryofDomicile","BareboatCharterCountryofRegistration","SafetyManagementCertificateDOCCompany","SafetyManagementCertificateIssuer","SafetyManagementCertificateDateIssued","SafetyManagementCertificateDateExpires"
"1007718","SIRONA III","In Service/Commission","538070201","V7JQ8","Marshall Islands","200602","Bikini","70201","Lloyd's Register 2004-01-16","Yacht","X11A2YP",152,914,274,0,0,56.500,47.166,.000,10.260,10.750,10.260,5.580,718,3.000,"Great Unknown","Nickel Corp Cayman Ltd","Fraser Yachts Florida Inc","Fraser Yachts Florida Inc","Megayacht Technical Services",0,0,0,"","","",0,0,0,,,,,,0,,,0,0,"",0,"1","Oceanfast Pty Ltd","2004","Australia","20010522","77",15.00,"","","","","","Unknown","","20040101",""
"","","","","","","","","",""
'''
    shipinspections = '''"LRNO","Inspection_ID","Authorisation","Shipname","CallSign","Flag","Class","Shiptype","Expanded_Inspection","Inspection_Date","Date_Release","No_Days_Detained","Port","Country","Owner","Manager","Charterer","Cargo","Detained","No_Defects","Source","GT","DWT","YOB","Other_Inspection_Type","Number_Part_Days_Detained","Follow_Up_Inspection"
"1000617","100061720110929","Paris MOU","ATLANTIC GOOSE ","V3MA","Belize","Lloyd's Register","Other Special Activities",False,2011-09-29 00:00:00,2011-09-29 00:00:00,,"Malta (Valletta)","Malta","","KOTA LTD.","","",False,"2         ","Paris MOU",352,,"","Initial Inspection",,""
'''
    shipdefects = '''"Defect_ID","Inspection_ID","Defect_text","DEFECT_CODE","ACTION_1","ACTION_2","ACTION_3","OTHER_ACTION","RECOGNISED_ORG_RESP_YN","RECOGNISED_ORG_RESP_CODE","RECOGNISED_ORG_RESP","OTHER_RECOGNISED_ORG_RESP","MAIN_DEFECT_CODE","MAIN_DEFECT_TEXT","ACTION_CODE_1","ACTION_CODE_2","ACTION_CODE_3","ClassIsResponsible","DetentionReasonDeficiency"
67642518,"100061720110929","Working and Living Conditions - Working Conditions - Protection machines/parts - Not as required","0820  ","","","","","N",,"","","0800  ","Working and Living Conditions","","","","","N"
67642519,"100061720110929","Fire safety - Means of escape - Not as required","0960  ","","","","","N",,"","","0900  ","Fire safety","","","","","N"
'''

    def test_insert_shipdata(self):

        mi_flag = Flag.objects.get_or_create(
            code="MHL",
            name="Marshall Islands",
            iso_3166_1_alpha_2="MH",
            world_continent="Oceania",
            world_region="Micronesia",
        )[0]

        self.assertEqual(ShipData.objects.count(), 0)

        input_file = StringIO(self.shipdata)
        import_file(input_file, ShipData)
        # self.assertEqual(Error.objects.count(), 0)

        data = ShipData.objects.get(imo_id='1007718')

        self.assertEqual(data.mmsi, '538070201')
        self.assertEqual(data.ship_name, 'SIRONA III')
        self.assertEqual(data.shiptype_level_5, 'Yacht')
        self.assertEqual(data.call_sign, 'V7JQ8')
        self.assertEqual(data.flag_name, 'Marshall Islands')
        self.assertEqual(data.flag.code, mi_flag.code)
        self.assertEqual(data.port_of_registry, 'Bikini')
        self.assertEqual(data.ship_status, 'In Service/Commission')
        self.assertEqual(data.gross_tonnage, 914.0)
        self.assertEqual(data.length_overall_loa, 56.500)
        self.assertEqual(data.year_of_build, 2004)
        self.assertEqual(data.registered_owner, 'Nickel Corp Cayman Ltd')
        self.assertEqual(data.operator, 'Fraser Yachts Florida Inc')
        self.assertEqual(data.ship_manager, 'Fraser Yachts Florida Inc')
        self.assertEqual(data.technical_manager, 'Megayacht Technical Services')
        self.assertEqual(data.group_beneficial_owner, 'Great Unknown')

        extradata = data.data
        expected = sorted(
            [
                "imo_id",
                "ship_name",
                "ship_status",
                "mmsi",
                "call_sign",
                "flag_name",
                "flag_effective_date",
                "port_of_registry",
                "official_number",
                "classification_society",
                "shiptype_level_5",
                "stat_code_5",
                "deadweight",
                "gross_tonnage",
                "net_tonnage",
                "panama_canal_net_tonnage_pcnt",
                "suez_canal_net_tonnage_scnt",
                "length_overall_loa",
                "length_between_perpendiculars_lbp",
                "breadth",
                "breadth_extreme",
                "breadth_moulded",
                "length_registered",
                "depth",
                "displacement",
                "draught",
                "group_beneficial_owner",
                "registered_owner",
                "operator",
                "ship_manager",
                "technical_manager",
                "bale_capacity",
                "gas_capacity",
                "grain_capacity",
                "insulated_capacity",
                "liquid_capacity",
                "number_of_cabins",
                "number_of_roro_lanes",
                "teu",
                "teu_capacity_14t_homogeneous",
                "segregated_ballast_capacity",
                "number_of_decks",
                "shipbuilder",
                "year_of_build",
                "country_of_build",
                "keel_laid_date",
                "yard_number",
                "speed",
                "safety_management_certificate_date_issued",
                "safety_management_certificate_doc_company",
            ]
        )
        self.assertEqual(sorted(extradata.keys()), expected)

    def test_update_shipdata(self):

        mi_flag = Flag.objects.get_or_create(
            code="MHL",
            name="Marshall Islands",
            iso_3166_1_alpha_2="MH",
            world_continent="Oceania",
            world_region="Micronesia",
        )[0]

        ShipData.objects.create(
            imo_id='1007718', ship_name='SIRONA', mmsi='538070201', data={}
        )
        data = ShipData.objects.get(imo_id='1007718')
        self.assertEqual(data.ship_name, 'SIRONA')

        input_file = StringIO(self.shipdata)
        import_file(input_file, ShipData)

        data = ShipData.objects.get(imo_id='1007718')

        self.assertEqual(data.mmsi, '538070201')
        self.assertEqual(data.ship_name, 'SIRONA III')
        self.assertEqual(data.shiptype_level_5, 'Yacht')
        self.assertEqual(data.call_sign, 'V7JQ8')
        self.assertEqual(data.flag_name, 'Marshall Islands')
        self.assertEqual(data.flag.code, mi_flag.code)
        self.assertEqual(data.port_of_registry, 'Bikini')
        self.assertEqual(data.ship_status, 'In Service/Commission')
        self.assertEqual(data.gross_tonnage, 914.0)
        self.assertEqual(data.length_overall_loa, 56.500)
        self.assertEqual(data.year_of_build, 2004)
        self.assertEqual(data.registered_owner, 'Nickel Corp Cayman Ltd')
        self.assertEqual(data.operator, 'Fraser Yachts Florida Inc')
        self.assertEqual(data.ship_manager, 'Fraser Yachts Florida Inc')
        self.assertEqual(data.technical_manager, 'Megayacht Technical Services')
        self.assertEqual(data.group_beneficial_owner, 'Great Unknown')

        extradata = data.data
        expected = sorted(
            [
                "imo_id",
                "ship_name",
                "ship_status",
                "mmsi",
                "call_sign",
                "flag_name",
                "flag_effective_date",
                "port_of_registry",
                "official_number",
                "classification_society",
                "shiptype_level_5",
                "stat_code_5",
                "deadweight",
                "gross_tonnage",
                "net_tonnage",
                "panama_canal_net_tonnage_pcnt",
                "suez_canal_net_tonnage_scnt",
                "length_overall_loa",
                "length_between_perpendiculars_lbp",
                "breadth",
                "breadth_extreme",
                "breadth_moulded",
                "length_registered",
                "depth",
                "displacement",
                "draught",
                "group_beneficial_owner",
                "registered_owner",
                "operator",
                "ship_manager",
                "technical_manager",
                "bale_capacity",
                "gas_capacity",
                "grain_capacity",
                "insulated_capacity",
                "liquid_capacity",
                "number_of_cabins",
                "number_of_roro_lanes",
                "teu",
                "teu_capacity_14t_homogeneous",
                "segregated_ballast_capacity",
                "number_of_decks",
                "shipbuilder",
                "year_of_build",
                "country_of_build",
                "keel_laid_date",
                "yard_number",
                "speed",
                "safety_management_certificate_date_issued",
                "safety_management_certificate_doc_company",
            ]
        )
        self.assertEqual(sorted(extradata.keys()), expected)

    def test_insert_shipinspection(self):
        self.assertEqual(ShipInspection.objects.count(), 0)

        input_file = StringIO(self.shipinspections)
        import_file(input_file, ShipInspection)

        data = ShipInspection.objects.get(imo_id='1000617')
        self.assertEqual(data.ship_name, 'ATLANTIC GOOSE')

    def test_insert_shipdefect(self):
        self.assertEqual(ShipInspection.objects.count(), 0)
        self.assertEqual(ShipDefect.objects.count(), 0)

        input_file = StringIO(self.shipinspections)
        import_file(input_file, ShipInspection)
        input_file = StringIO(self.shipdefects)
        import_file(input_file, ShipDefect)

        data = ShipInspection.objects.get(imo_id='1000617')
        self.assertEqual(data.ship_name, 'ATLANTIC GOOSE')

    def test_update_modified_ship_shipdata(self):

        Flag.objects.get_or_create(
            code="MHL",
            name="Marshall Islands",
            iso_3166_1_alpha_2="MH",
            world_continent="Oceania",
            world_region="Micronesia",
        )

        created_ship = ShipData.objects.create(
            imo_id='1007718', ship_name='SIRONA', mmsi='538070201', data={}
        )
        data = ShipData.objects.get(imo_id='1007718')
        self.assertEqual(data.ship_name, 'SIRONA')

        ShipDataManualChangeFactory.create(
            changed_ship=created_ship,
            old_data={'ship_name': 'SIRONA III'},
            new_data={'ship_name': 'ZLOMRONA'},
        )

        input_file = StringIO(self.shipdata)
        _, seen_ids = import_file(input_file, ShipData)
        apply_manual_changes_on_ship_data(imos_seen=seen_ids)

        data = ShipData.objects.get(imo_id='1007718')

        self.assertEqual(data.mmsi, '538070201')
        self.assertEqual(data.ship_name, 'ZLOMRONA')
        self.assertEqual(data.shiptype_level_5, 'Yacht')
        self.assertEqual(data.call_sign, 'V7JQ8')
        self.assertEqual(data.flag_name, 'Marshall Islands')


class SetupIhsConnectionTest(TestCase):
    @patch('ships.connectors.FTP')
    @override_settings(IHS_REMOTE_DIR='/directory/')
    def test_ftpconnector_instantiation(self, mock_ftp):
        FTPConnector(
            host=settings.IHS_HOST,
            user=settings.IHS_USER,
            passwd=settings.IHS_PASSWORD,
            pasv=True,
            work_dir='/',
        )
        mock_ftp.assert_called_once_with(settings.IHS_HOST)
        mock_ftp.return_value.login.assert_called_once_with(
            settings.IHS_USER, settings.IHS_PASSWORD
        )
        mock_ftp.return_value.cwd.assert_called_once()


class SynchroniseFilesTest(TestCase):
    def setUp(self):
        self.testfname = str(uuid.uuid4()) + '.zip'
        self.dir = '/tmp/sis_test/'
        self.test_fullfn = dst = os.path.join('/tmp/', self.testfname)
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

        src = os.path.join(
            settings.PROJECT_ROOT, 'ships/tests/data/test_shipdata_20140804.zip'
        )
        shutil.copyfile(src, dst)
        self.factoried_ship_data = ShipDataFactory.create()

    def tearDown(self):
        if os.path.isfile(self.test_fullfn):
            os.unlink(self.test_fullfn)
        os.rmdir(self.dir)

    @patch('ships.connectors.FTP')
    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND='memory',
        IHS_CACHE_DIR='/tmp/',
        CONNECTOR_TYPE='FTP',
    )
    def test_synchronise_files(self, mock_setup_ftp):

        mock_ftp = mock_setup_ftp.return_value
        mock_ftp.nlst.return_value = [self.testfname]
        mock_ftp.retrbinary.return_value = '226'

        synchronise_files()

        mock_setup_ftp.assert_called_once()
        self.assertEqual(mock_ftp.nlst.call_count, 3)
        mock_ftp.close.assert_called_once()

        self.assertEqual(3, LoadStatus.objects.all().count())
        for ls in LoadStatus.objects.all():
            self.assertEqual(LoadStatus.SUCCEEDED, ls.status)

        self.assertEqual(1, LoadHistory.objects.all().count())
        self.assertEqual(LoadHistory.SUCCEEDED, LoadHistory.objects.all()[0].status)

        self.assertEqual(0, ShipDefect.objects.all().count())
        self.assertEqual(1485, ShipInspection.objects.all().count())
        self.assertLess(67, ShipData.objects.all().count())
        self.assertEqual(99, ShipMovement.objects.all().count())

    @patch('ships.connectors.SFTPClient')
    @patch('ships.connectors.Transport')
    @override_settings(IHS_CACHE_DIR='/tmp/', CONNECTOR_TYPE='SFTP')
    def test_synchronise_files_over_sftp(self, mock_transport, mock_sftp_client):
        # Given: one file and folder resides in each remote directory.
        file_name = str(uuid.uuid4())
        file_obj = SFTPAttributes()
        file_obj._flags = 13
        file_obj.st_size = 443051
        file_obj.st_uid = None
        file_obj.st_gid = None
        file_obj.st_mode = 33279
        file_obj.st_atime = 1597813556
        file_obj.st_mtime = 1597813556
        file_obj.attr = {}
        file_obj.filename = file_name
        file_obj.longname = (
            f'-rwxrwxrwx 1 0        0             443051 Aug 19 06:05 {file_name}'
        )

        dir_name = str(uuid.uuid4())
        directory = SFTPAttributes()
        directory._flags = 13
        directory.st_size = 0
        directory.st_uid = None
        directory.st_gid = None
        directory.st_mode = 16895
        directory.st_atime = 1460005344
        directory.st_mtime = 1460005344
        directory.attr = {}
        directory.filename = dir_name
        directory.longname = (
            f'drwxrwxrwx 1 0        0                  0 Apr 07  2016 {dir_name}'
        )

        mock_sftp_client.from_transport.return_value.listdir_attr.return_value = [
            file_obj,
            directory,
        ]

        # When: sync of files launches.
        synchronise_files()

        # Then: Transport instance creates a connection to a remote host.
        mock_transport.assert_called_once()
        mock_transport.return_value.connect.assert_called_once()

        # And: SFTPClient uses the instance as a gateway to connect SFTP
        # server.
        mock_sftp_client.from_transport.assert_called_once()

        # And: the client changes a working directory, shows files only inside
        # it and downloads them.
        mock_sftp_client.from_transport.return_value.chdir.assert_called_once()
        mock_sftp_client.from_transport.return_value.listdir_iter.called
        mock_sftp_client.from_transport.return_value.get.assert_called()

        # And: Transport instance closes the connection to SFTP server.
        mock_sftp_client.from_transport.return_value.close.assert_called_once()
        mock_transport.return_value.close.assert_called_once()

    @patch('ships.connectors.FTP', autospec=True)
    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND='memory',
        IHS_CACHE_DIR='/tmp/',
    )
    def test_synchronise_and_apply_manual_changes(self, mock_setup_ftp):
        manual_change = ShipDataManualChangeFactory.create(
            changed_ship=self.factoried_ship_data
        )
        apply_manual_changes_on_ship_data(imos_seen=[manual_change.changed_ship.imo_id])

        self.assertEqual(1, ShipData.objects.all().count())
        updated_ship_data = ShipData.objects.last()
        self.assertEqual(updated_ship_data.registered_owner, 'Scrooge Inc.')
        self.assertEqual(updated_ship_data.data['registered_owner'], 'Scrooge Inc.')
        self.assertEqual(
            updated_ship_data.original_data, {"immah_random_data_key": "Imma value"}
        )

    @patch('ships.connectors.FTP', autospec=True)
    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND='memory',
        IHS_CACHE_DIR='/tmp/',
    )
    def test_synchronise_and_not_matching_manual_changes(self, mock_setup_ftp):
        manual_change = ShipDataManualChangeFactory.create(
            changed_ship=self.factoried_ship_data,
            old_data={'port_of_registry': 'Denver'},
            new_data={'port_of_registry': 'Prague'},
        )
        apply_manual_changes_on_ship_data(imos_seen=[manual_change.changed_ship.imo_id])

        self.assertEqual(1, ShipData.objects.all().count())
        updated_ship_data = ShipData.objects.last()
        manual_change_object = ShipDataManualChange.objects.last()
        # Let's make sure that it didn't change
        self.assertEqual(
            self.factoried_ship_data.port_of_registry,
            updated_ship_data.port_of_registry,
        )
        self.assertEqual(manual_change_object.expired, True)

    @patch('ships.connectors.FTP', autospec=True)
    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND='memory',
        IHS_CACHE_DIR='/tmp/',
    )
    def test_synchronise_expired_entry(self, mock_setup_ftp):
        manual_change = ShipDataManualChangeFactory.create(
            changed_ship=self.factoried_ship_data,
            old_data={'port_of_registry': 'Graz'},
            new_data={'port_of_registry': 'Prague'},
        )
        apply_manual_changes_on_ship_data(imos_seen=[manual_change.changed_ship.imo_id])

        self.assertEqual(1, ShipData.objects.all().count())
        updated_ship_data = ShipData.objects.last()
        # Let's make sure that it didn't change
        self.assertEqual(
            self.factoried_ship_data.port_of_registry,
            updated_ship_data.port_of_registry,
        )
        change_object = ShipDataManualChange.objects.last()
        self.assertEqual(change_object.expired, True)

    @patch('ships.connectors.FTP', autospec=True)
    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND='memory',
        IHS_CACHE_DIR='/tmp/',
    )
    def test_synchronise_partially_expired_entry(self, mock_setup_ftp):
        manual_change = ShipDataManualChangeFactory.create(
            changed_ship=self.factoried_ship_data,
            old_data={
                'port_of_registry': 'Graz',
                'registered_owner': 'Denver Maritime Ltd',
            },
            new_data={
                'port_of_registry': 'Prague',
                'registered_owner': 'Aperture Laboratories',
            },
        )
        apply_manual_changes_on_ship_data(imos_seen=[manual_change.changed_ship.imo_id])

        self.assertEqual(1, ShipData.objects.all().count())
        updated_ship_data = ShipData.objects.last()
        # Let's make sure that it didn't change
        self.assertEqual(
            self.factoried_ship_data.port_of_registry,
            updated_ship_data.port_of_registry,
        )
        change_object = ShipDataManualChange.objects.last()
        self.assertEqual(change_object.expired, False)
