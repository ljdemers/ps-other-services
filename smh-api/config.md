## environment configuration for the SMH Service

- API_PASSWORD default super-fast

    The basic auth password.

- DB_HOST default 172.16.21.45

    The DB host.

- DB_PORT default 5432

    The DB port.

- DB_NAME default bi

    The DB name.

- DB_USER default bi

    The DB user.

- DB_PASSWORD default noan7wiu9OoF

    The DB password.

- DB_TYPE default RDS 

    The DB Engine to use (RDS or DOCUMENT_DB).
    
- AIS_REST_BASE_URL default http://internal-prod-ais-elasticlo-1et06hcch616u-2099117978.us-east-1.elb.amazonaws.com/api/v2

    AIS service url

- AIS_USERNAME default admin

    AIS service url

- AIS_PASSWORD default secret

    AIS service url

- SIS_BASE_URL default https://sis.polestar-production.com/api/v1

    The FQDN of the SIS API.

- SIS_USERNAME default smh

    The user to connect to the SIS service with.

- SIS_API_KEY mandatory

    The API key for SIS user.

- PORT_SERVICE_BASE_URL default ports-api.polestar-testing.com:50051

    The portservice URL
    
- PORT_SERVICE_MESSAGE_VERSION default 2.3

    The portservice message version (new = 2.3)     

- AIS_MAX_POSITIONS_FOR_SCREENING default 500000

    Max number of AIS positions for SMH

- STATSD_HOST default localhost

    The host name of the statsd server to receive statistics.

- STATSD_PORT default 8125

    The UDP port of the statds service.

- STATSD_PREFIX default smh

    The prefix to use for statistics written to statsd.

- LOG_LEVEL default DEBUG

    The logging level for the service.

- ENVIRONMENT default test

    The application environment where the service is running in.

- CASSANDRA_SERVERS default test

    The comma separated list of IP addresses of seed server in the Cassandra
    cluster.  The value 'test' will prevent settings from attempting
    to establish a connection to the cluster.

- CASSANDRA_KEYSPACE default ais20

    The Keyspace that the AIS tables reside in the Cassandra cluster.

- CASSANDRA_AWS mandatory

    Cassandra AWS instance # cassandra.us-east-1.amazonaws.com

- CASSANDRA_KEYSPACE_AUTH_CERT_PATH default certs/sf-class2-root.crt

    Path to locate authentication certificate

- CASSANDRA_KEYSPACE_USERNAME mandatory

    Username for production Cassandra Keyspace

- CASSANDRA_KEYSPACE_PASSWORD mandatory

    Password for production Cassandra Keyspace

- CASSANDRA_PORT default 9142

    Port used by Cassandra

- KEYSPACE_CUT_OFF_DATE default 2022-06-08T00:00:00Z

    The date from which to get data from Keyspace. Queries for data older than this date
    will revert to the Cassandra database for trail data(gradually increase this date
    in the past on a certain period of time).

- USE_AISAPI default True

    Flag that controls the use of Cassandra/Keyspaces backend as a data source or existing
    AISAPI endpoints

- DEFAULT_DOWNSAMPLE_FREQUENCY_SECONDS default 600

    down sampling frequency to use in AISAPI

- DOWNSAMPLE_USER_LIST default screening,system

    Comma seperated list of API users who has downsampling enabled (NONE, All or list of users, default: screening and system users)
