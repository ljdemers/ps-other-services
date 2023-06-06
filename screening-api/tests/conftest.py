from os import path


def pytest_addoption(parser):
    group = parser.getgroup('flask')
    group._addoption(
        '--ini-file',
        action='store',
        type='string',
        default='screening_api/confs/test.ini',
        help=(
            'INI file path, i.e.: '
            '"py.test --ini-file test.ini ." '
            'or "py.test --ini-file=test.ini"'
        )
    )


def pytest_configure(config):
    ini_path = config.getoption('ini_file')
    here = path.dirname(__file__)
    project_dir = path.dirname(here)
    config_path = path.join(project_dir, ini_path)
    if not path.exists(config_path):
        raise ValueError('Config %s not found!' % config_path)
