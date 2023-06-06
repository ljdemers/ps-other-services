from unittest import mock
import pytest
import datetime
from screening_workers.lib.utils import date2str, str2date, json_logger


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
        test_date = str2date(test_date_string, "%Y/%m/%d %H %M")
        assert expected == test_date

        # custom format - two formats in tuple
        test_date_string = "2017/08/10 05 58 50"
        expected = datetime.datetime(2017, 8, 10, 5, 58, 50)

        test_date = str2date(test_date_string,
                             ("%Y/%m/%d %H %M", "%Y/%m/%d %H %M %S"))
        assert expected == test_date

        expected = datetime.datetime(2017, 8, 10, 5, 58, 50, 787876)
        test_date_string = "2017-08-10T05:58:50.787876"  # Full format
        test_date = str2date(test_date_string)
        assert expected == test_date

        # 'test_date_string' is not the default date format
        test_date_string = "2017/08/10 05 58 50"
        with pytest.raises(ValueError):
            str2date(test_date_string)

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
