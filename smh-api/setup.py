from pathlib import Path
from setuptools import find_packages, setup
from smh_service import __author__, __email__, __url__, __version__


def read_requirements(filename):
    contents = Path(filename).read_text().strip('\n')
    return [line for line in contents.split('\n') if not line.startswith('-')]


setup(
    name='smh-api',
    author=__author__,
    author_email=__email__,
    version=__version__,
    url=__url__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements('requirements.txt'),
    extras_require=dict(tests=read_requirements('requirements-dev.txt')),
)
