"""
Ties together all the tasks for running the celery worker that is imported in
`sis_api/__init__.py` so tasks are available if SiS package is imported by
celery worker e.g. celery worker -A sis
"""

import os

from celery import Celery

from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sis_api.settings.base')

app = Celery('sis_api')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
