Screening Workers
=================

Screening Workers is responsible for generating screening reports and processing all the
other background tasks related to screening.

Actual checks:
 * Company sanctions
 * Country sanctions
 * Ship inspections
 * Ship sanctions
 * Ship movement history

Docker environment
------------------

To use docker test environment run the following command:

::

    $ docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d

Stop and remove containers when finished work:

::

    $ docker-compose -f docker-compose.yml -f docker-compose.test.yml down

Testing
-------

Use the following command to run tests: 

::

    $ python setup.py test

Or run tests inside docker container. Start docker test environment before
executing tests (See `Docker environment`). Use the following command to run tests:

::

    $ docker-compose exec consumers python setup.py test

Building
--------

Screening Workers packages are based on `wheel standard <http://pythonwheels.com>`_.
In order to build `wheel <http://pythonwheels.com>`_ package run
the following command: 

::

    $ pip install wheel
    $ python setup.py bdist_wheel

or build inside docker container. Start docker test environment before
executing tests (See `Docker environment`). Then use the following command:

::

    $ docker-compose exec consumers python setup.py bdist_wheel

Use of Private Python packages outside Docker containers
--------------------------------------------------------

If you want to install, for instance, screening-api package with version x.y.z
then you have to have configured `awscli`, see
`documentation <https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html>`_.

The next step is to generate a CodeArtifact token to install a Python package
from our private, AWS CodeArtifact repository,
`see this <https://docs.aws.amazon.com/codeartifact/latest/ug/using-python.html>`_.
You only need to do this step if you're not going to make use Makefile targets.
Otherwise go to the next paragraph.

If you want to upload a Python package to a private repository then you need
to install twine, wheel, and setuptools (assumes you have got configured awscli):

Steps for a host machine:

::

    $ pip install -r requirements_dev.txt
    $ make dist-cleanup
    $ make dist-build
    $ make dist-upload

Steps for Docker:

::

    $ make compose-dist-cleanup
    $ make compose-dist-build
    $ make compose-dist-upload

Last but not least, make sure you don't mix up compose with host commands
because you may end up with a situation where it says you need `sudo`
permissions to delete a directory.

Versioning
----------

Screening API uses `bumpversion <https://pypi.python.org/pypi/bumpversion>`_
package to manager versioning. In order to release new version run the following command: 

::

    $ pip install bumpversion
    $ bumpversion release --tag

You can also bump other parts of version.

Version bumps with examples:
 * ``bumpversion patch``: ``0.1.0 -> 0.1.1rc0``
 * ``bumpversion release```: ``0.1.1rc0 -> 0.1.1``
 * ``bumpversion minor``: ``0.1.1 -> 0.2.0rc0``
 * ``bumpversion rc``: ``0.2.0rc0 -> 0.2.0rc1``
 * ``bumpversion release``: ``0.2.0.dev1 -> 0.2.0``

.. warning::

    Each version bump will also create commit.
