# SMH Service
A service to compute ship movement history(SMH) using AIS, SIS and port service.
Use stored/cached results if a ship is already been screened before.
It has option to have MMSI history, joining IHS movement data,
outliers detection, speed filtering, multiple AIS position rate, etc.

### Run the application

```
$> docker-compose build && docker-compose up
```

Read content of files in  `docker/` to have an idea of libraries installed and commands executed.


### Docker commands

* `docker-compose build && docker-compose up` will get up and running a
   SMH service instance for you, available at http://localhost:8080
* `docker-compose kill` will terminate that running instance.
* `docker-compose rm -f` will remove the remaining containers from your system
   after shutting down a running instance. This is useful to keep your disk and
   memory clean and also to make sure you raise fresh new instances after you
   change some code.
* `docker-compose run smh-api pytest`
   will run the unit tests for the whole project. If you want test coverage as
   well, the command also accepts regular Nose suite arguments.

## Configuration

The following table lists the configurable environment variables.

| Environment Variable              | Description                                | Default                                                   |
| --------------------------------- | ------------------------------------------ | --------------------------------------------------------- |
| `API_PASSWORD`                    | SMH API password                           | `super-fast`                                     |
| `AIS_MAX_POSITIONS_FOR_SCREENING` | AIS max positions for screening            | `500000`                                                  |
| `AIS_BASE_URL`                    | AIS API base url                           | `http://commaisservice.polestarglobal-test.com/api/v2`    |
| `AIS_USERNAME`                    | AIS API username                           | `admin`                                                   |
| `AIS_Password`                    | AIS API password                           | `secret`                                                  |
| `SIS_BASE_URL`                    | SIS API base url                           | `https://sis.polestar-testing.com/api/v1`                 |
| `SIS_USERNAME`                    | SIS API username                           | `purpletrac`                                              |
| `SIS_API_KEY`                     | SIS API key                                | `b85d85a9523e7caf3ecec776b003f3c91e84aa94`                |
| `PORT_SERVICE_BASE_URL`           | Ports API URL                              | `ports-api.polestar-staging.com:50051`                    |     

Some others are listed in config.md file.

## Versioning

SMH service uses [bumpversion] package to manager versioning. In order to release new version run the following command: 

    $ pip install bump2version
    $ bump2version release --tag
    $ git push

You can also bump other parts of version.

### Version bumps with examples:

 - `bump2version patch`: `0.1.0 -> 0.1.1rc0`
 - `bump2version release`: `0.1.1rc0 -> 0.1.1`
 - `bump2version minor`: `0.1.1 -> 0.2.0rc0`
 - `bump2version rc`: `0.2.0rc0 -> 0.2.0rc1`
 - `bump2version release`: `0.2.0rc1 -> 0.2.0`
 