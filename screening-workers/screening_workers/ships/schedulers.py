"""Screening workers ships schedulers module"""


class ShipCacheUpdateScheduler:

    def __init__(self, task):
        self.task = task

    def schedule(self, ship_id: int):
        self.task.apply_async((ship_id, ))
