"""Screening API wsgi module"""
import os

from screening_api.main import create_app

app = create_app(os.environ)
