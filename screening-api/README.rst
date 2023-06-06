Screening API
=============

Screening API is resposible for reports that detect sanctions,
compliance violations and other risky behavior.

Actual checks:
 * Company sanctions
 * Country sanctions
 * Ship inspections
 * Ship sanctions
 * Ship movement history

API Documentation
-----------------

The API documentation is based on `OpenAPI 3.0.0 specification <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md>`_


To view the documentation run: 

::

    $ docker-compose up api-ui

and go under http://localhost:8080/

Docker environment
------------------

To use docker environment run the following command:

::

    $ docker-compose up -d

There is also docker test environment suitable to run tests. To use docker 
test environment run the following command:

::

    $ docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d

Stop and remove containers when finished work:

::

    $ docker-compose down

Configuration
-------------

The following table lists the configurable environment variables.

===================================  ===========================================  =========================================================
      **Environment Variable**                      **Description**                                       **Default**                       
-----------------------------------  -------------------------------------------  ---------------------------------------------------------
``INI_FILE``                           INI file with logging config (required)    (not set)                                    
``JWT_SECRET``                         JWT authentication secret (required)       (not set)
``DBBACKEND``                          Database backend                           ``postgresql+psycopg2``
``DBUSER``                             Database user                              ``screening``
``DBPASSWORD``                         Database password                                                              
``DBHOST``                             Database host                              ``localhost``                                             
``DBNAME``                             Database name                              ``screening``                                    
``DBPORT``                             Database port                              ``5432``                                             
``BROKERBACKEND``                      Broker backend                             ``redis``                                    
``BROKERUSER``                         Broker user                                                                             
``BROKERPASSWORD``                     Broker password                                                                
``BROKERHOST``                         Broker host                                ``localhost``                                             
``BROKERNAME``                         Broker name                                ``0``                                    
``BROKERPORT``                         Broker port                                ``6379``                                           
``BROKER_CONNECTIONS_LIMIT``           Broker connections limit                   ``100``
``CACHEBACKEND``                       Cache backend                              ``redis``                                    
``CACHEUSER``                          Cache user                                                                              
``CACHEPASSWORD``                      Cache password                                                                 
``CACHEHOST``                          Cache host                                 ``localhost``                                             
``CACHENAME``                          Cache name                                 ``3``                                    
``CACHEPORT``                          Cache port                                 ``6379``     
``AWS_XRAY_TRACING_NAME``              AWS X-Ray tracing name                          
``AWS_XRAY_CONTEXT_MISSING``           AWS X-Ray context missing                  ``RUNTIME_ERROR``     
``AWS_XRAY_DAEMON_ADDRESS``            AWS X-Ray daemon address                   ``127.0.0.1:2000``     
===================================  ===========================================  =========================================================

Testing
-------

Use the following command to run tests: 

::

    $ python setup.py test

Or run tests inside docker container. Start docker test environment before
executing tests (See `Docker environment`_). Use the following command to run tests:

::

    $ docker-compose exec api python setup.py test

Test data
---------

Screening API provides CLI tool for generating test data.
In order to generate data use the following command:

::

    $ ./bin/testdata-gen

or run inside docker container. Start docker test environment before
running command (See `Docker environment`_). Then use the following command:

::

    $ docker-compose exec api testdata-gen

Test data generator usage:

::

    usage: testdata-gen [-h] [--verbose] {ships,screenings} ...

    Test data generator.

    positional arguments:
    {ships,screenings}  data type

    optional arguments:
    -h, --help          show this help message and exit
    --verbose, -v

Supported data types generators:

- ships generator

::

    $ # creates 3 ships
    $ docker-compose exec api testdata-gen ships 3
    $ # creates ship with imo id 12345
    $ docker-compose exec api testdata-gen ships 1 --imo_id 12345

- screenings generator

::

    $ # creates 4 screenings for account ID 12
    $ docker-compose exec api testdata-gen screenings 4 --account_id 12
    $ # creates 2 screenings for account ID 12 with severity OK
    $ docker-compose exec api testdata-gen screenings 4 --account_id 12 --severity 20-ok
    $ # creates 3 screenings for account ID 12 with ship id 21
    $ docker-compose exec api testdata-gen screenings 4 --account_id 12 --ship_id 21

- screenings history generator

::

    $ # creates 4 screenings history for screening ID 12
    $ docker-compose exec api testdata-gen history 4 --screening_id 12
    $ # creates 2 screenings history for screening ID 12 with severity OK
    $ docker-compose exec api testdata-gen history 4 --screening_id 12 --severity 20-ok

Postman testing
---------------

Start docker test environment before executing tests (See `Docker environment`_).
Use the following command to run Postman tests:

::

    $ docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm api-postman

Building
--------

Screening API packages are based on `wheel standard <http://pythonwheels.com>`_.
In order to build `wheel <http://pythonwheels.com>`_ package run
the following command: 

::

    $ pip install wheel
    $ python setup.py bdist_wheel

or build inside docker container. Start docker test environment before
executing tests (See `Docker environment`_). Then use the following command:

::

    $ docker-compose exec api python setup.py bdist_wheel

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
 * ``bumpversion release``: ``0.2.0rc1 -> 0.2.0``

.. warning::

    Each version bump will also create commit.
