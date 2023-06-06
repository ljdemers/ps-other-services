from unittest import mock
import pytest
import datetime
from api_clients.utils import date2str, str2date, \
    json_logger, convert_float, json_unzip, json_zip, ZIPJSON_KEY


class TestUtils:
    def test_date2str(self):
        # test normal date
        test_date = datetime.datetime(2017, 8, 10, 5, 58, 50)
        test_date_string = date2str(test_date)
        expected = "2017-08-10T05:58:50Z"
        assert expected == test_date_string

    def test_date2str_exception(self):
        with pytest.raises(TypeError):
            date2str(None)
        with pytest.raises(TypeError):
            date2str("ABC")

    def test_str2date(self):
        expected = datetime.datetime(2017, 8, 10, 5, 58, 50)
        expected_date = datetime.datetime(2017, 8, 10, 0, 0, 0)

        test_date_string = "2017-08-10T05:58:50Z"  # default format
        test_date = str2date(test_date_string)
        assert expected == test_date

        test_date_string = "2017-08-10T05:58:50"  # auto fallback format
        test_date = str2date(test_date_string)
        assert expected == test_date

        test_date_string = "2017-08-10"  # auto fallback format - just date
        test_date = str2date(test_date_string)
        assert expected_date == test_date

        test_date_string = "2017/08/10 05 58"  # custom format - no sec
        expected = datetime.datetime(2017, 8, 10, 5, 58, 0)
        test_date = str2date(test_date_string, False, "%Y/%m/%d %H %M")
        assert expected == test_date

        # timezone aware
        test_date = str2date(test_date_string, True, "%Y/%m/%d %H %M")
        assert expected.replace(tzinfo=datetime.timezone.utc) == test_date

        # custom format - two formats in tuple
        test_date_string = "2017/08/10 05 58 50"
        expected = datetime.datetime(2017, 8, 10, 5, 58, 50)

        test_date = str2date(test_date_string, False,
                             ("%Y/%m/%d %H %M", "%Y/%m/%d %H %M %S"))
        assert expected == test_date

        # 'test_date_string' is not the default date format return None
        test_date = str2date(test_date_string)
        assert test_date is None

        expected = datetime.datetime(2017, 8, 10, 5, 58, 50, 787876)
        test_date_string = "2017-08-10T05:58:50.787876"  # Full format
        test_date = str2date(test_date_string)
        assert expected == test_date

    def test_json_logger(self):
        import structlog

        logger = json_logger(__name__,
                             'INFO')  # use the current module for name
        logger.info('This have logger name = test_util and on one line?')
        logger.debug('This is not shown!')

        logger = json_logger(name='my_module', level='DEBUG',
                             indent=4)  # use the provided name
        logger.debug(
            'This have logger name = '
            'my_module and multi-line with indent of 4?'
        )

        with mock.patch('structlog.processors.JSONRenderer', mock.MagicMock()):
            logger = json_logger('test')

            assert isinstance(logger._processors[1],
                              type(structlog.stdlib.filter_by_level)) is True
            assert isinstance(logger._processors[2],
                              type(structlog.stdlib.add_log_level)) is True
            assert structlog.processors.JSONRenderer.call_args[1][
                       'indent'] is None

            json_logger('test', indent=4)
            assert structlog.processors.JSONRenderer.\
                call_args[1]['indent'] == 4

    def test_convert_float(self):
        value = None  # can't convert, return as is
        assert convert_float(value) == value

        value = 'abc'  # can't convert, return as is
        assert convert_float(value) == value

        value = '12.34456'  # can convert
        assert convert_float(value) == float(value)

        value = '-46'  # can convert
        assert convert_float(value) == float(value)


class TestJsonZipMethods:
    # Unzipped
    unzipped = {"a": "A", "b": "B"}

    # Zipped
    zipped = {ZIPJSON_KEY: "eJyrVkpUslJyVNJRSgLSTkq1ACPXA+8="}

    # List of items
    items = [123, "123", unzipped]

    def test_json_zip(self):
        assert self.zipped == json_zip(self.unzipped)

    def test_json_unzip(self):
        assert self.unzipped == json_unzip(self.zipped)

    def test_json_zipunzip(self):
        for item in self.items:
            assert item == json_unzip(json_zip(item))

    def test_json_zipunzip_chinese(self):
        item = {'hello': "你好"}
        assert item == json_unzip(json_zip(item))

    def test_json_unzip_insist_failure(self):
        for item in self.items:
            with pytest.raises(RuntimeError):
                json_unzip(item, insist=True)

    def test_json_unzip_noinsist_justified(self):
        for item in self.items:
            assert item == json_unzip(item, insist=False)

    def test_json_unzip_noinsist_unjustified(self):
        assert self.unzipped == json_unzip(self.zipped, insist=False)
