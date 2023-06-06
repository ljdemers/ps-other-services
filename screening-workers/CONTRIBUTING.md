# Contributing

This doc should be read as a brain dump of any relevant information you might
want in addition to the README file.

The worker project is just a celery project comprising a number of tasks to
perform a screening of a ship.

## Architecture

The screening project follows constructor based dependency injection.
Routing of dependencies can be viewed in `screening_workers.main.setup_app`.

### Signposts
The entry point for a screening task is
`screening_worker.screenings_bulk.tasks.BulkScreeningValidationTask`.  This in
turn triggers (through a signal)
`screening_workers.screenings.schedulers.ScreeningScheduler` which starts a
screening by triggering the required checks asynchronously.


### anatomy of a check
The general pattern for checks is:
```
Task
  Check:
    Report:
    *Repository/collection:
      db/services
```

A Task is linked to a corresponding Check.
A Check can have a number of repositories/collections that wrap db/api resources
respectively.
Most checks also include a Report, which manages serialisation of the provided
data sources into fields relevant to the check for reporting or display to the
user.
