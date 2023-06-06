"""Screening Workers celery module"""
import os
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from screening_workers.main import create_app

app = create_app(os.environ)

if __name__ == '__main__':
    # To disable this warning on API requests:
    # "InsecureRequestWarning: Unverified HTTPS request is being
    # made. Adding certificate verification is strongly advised."
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    app.start()
