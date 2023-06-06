# Ship Information System - importer and a REST API

Company called IHS Global Limited has a product called "IHS Fairplay Sea-web™
which is an online register of ships.
http://www.sea-web.com/seaweb_key_features.html
http://www.ihs.com/products/maritime-information/ships/sea-web.aspx

Celerybeat scheduler task `ships.tasks.synchronise_files`
synchronizes csv files in latin-1 encoding with IHS FTP server
and loads the data they contain.
`LoadStatus` model keeps info about each import.
Attribute translation is done via seaweb.translate.
Imported data is saved in Django models (`ShipData`, `ShipInspection`, `ShipDefect`...)
and exposed through a TastyPie based REST API (`ShipResource`, `ShipInspectionsResource`...)

## Running tests

    export DJANGO_SETTINGS_MODULE=development_settings.paul_bielecki
    export PYTHONPATH=${PYTHONPATH}:/home/pgb/workspace/sis-api
    virtualenv venv
    . venv/bin/activate
    pip install -r requirements.txt
    ./manage.py test

## Versioning

Screening API uses [bumpversion](https://pypi.python.org/pypi/bumpversion)
package to manager versioning. In order to release new version run the following command: 

```
    $ pip install bumpversion
    $ bumpversion release
```

You can also bump other parts of version.

Version bumps with examples:

* ``bumpversion patch``: ``0.1.0 -> 0.1.1rc0``
* ``bumpversion release```: ``0.1.1rc0 -> 0.1.1``
* ``bumpversion minor``: ``0.1.1 -> 0.2.0rc0``
* ``bumpversion rc``: ``0.2.0rc0 -> 0.2.0rc1``
* ``bumpversion release``: ``0.2.0rc1 -> 0.2.0``

**warning**

    Each version bump will also create commit with tag
