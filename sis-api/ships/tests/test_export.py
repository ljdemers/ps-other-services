from unittest.mock import mock_open, patch

from django.db import DataError
from django.test import TestCase

from ships.export import export_file_for_globavista, file_size


class TestFileSize(TestCase):
    def test_with_file(self):
        self.assertTrue(file_size(__file__) > 0)

    def test_with_missing_file(self):
        self.assertTrue(file_size('/tmp/file/wot/is/made/up.jpg') == 0)


class TestExportFileForGlobaVista(TestCase):

    def setUp(self):
        super().setUp()
        self.target_filename = '/tmp/output_file.csv'

        self.open_data = mock_open()
        self.mock_open = patch('ships.export.open', self.open_data).start()

        self.lzma_data = mock_open()
        self.mock_lzma_open = patch(
            'ships.export.lzma.open',
            self.lzma_data
        ).start()

        self.mock_file_size = patch('ships.export.file_size').start()
        self.mock_file_size.return_value = 100

    def test_create_export(self):
        target_filename = export_file_for_globavista(
            target_filename=self.target_filename,
            lzma_compressed=False
        )

        self.assertEqual(target_filename, self.target_filename)
        self.open_data.assert_called_once_with(self.target_filename, 'w')
        self.open_data.return_value.write.assert_called_once()
        self.lzma_data.assert_not_called()
        self.mock_file_size.assert_called_once_with(self.target_filename)

    def test_create_compressed_export(self):
        compressed_filename = f'{self.target_filename}.xz'

        target_filename = export_file_for_globavista(
            target_filename=self.target_filename,
            lzma_compressed=True
        )

        self.assertEqual(target_filename, compressed_filename)
        self.open_data.assert_not_called()
        self.lzma_data.assert_called_once_with(compressed_filename, 'w')
        self.lzma_data.return_value.write.assert_called_once()
        self.mock_file_size.assert_called_once_with(compressed_filename)

    @patch('ships.export.Path', side_effect=FileNotFoundError)
    def test_missing_sql_file(self, mock_path):
        target_filename = export_file_for_globavista(
            target_filename=self.target_filename,
            lzma_compressed=False
        )

        self.assertIsNone(target_filename)
        self.open_data.assert_not_called()
        self.lzma_data.assert_not_called()
        self.mock_file_size.assert_not_called()

    def test_target_folder_does_not_exist(self):
        self.open_data.side_effect = FileNotFoundError

        target_filename = export_file_for_globavista(
            target_filename=self.target_filename,
            lzma_compressed=False
        )

        self.assertIsNone(target_filename)
        self.open_data.assert_called_once_with(self.target_filename, 'w')
        self.lzma_data.assert_not_called()
        self.mock_file_size.assert_not_called()

    @patch('ships.export.connection')
    def test_db_error(self, mock_connection):
        mock_connection.cursor.side_effect = DataError

        target_filename = export_file_for_globavista(
            target_filename=self.target_filename,
            lzma_compressed=False
        )

        self.assertIsNone(target_filename)
        self.open_data.assert_not_called()
        self.lzma_data.assert_not_called()
        self.mock_file_size.assert_not_called()
