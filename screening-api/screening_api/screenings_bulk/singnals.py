"""Screening API screenings bulk signals module"""
from blinker import Signal

bulk_save_screenings = Signal('bulk_save_screenings')
