from celery import Celery
from celery.app.registry import TaskRegistry


class CheckTasksRegistry(dict):

    @classmethod
    def create(cls, *tasks):
        data = {task.name: task for task in tasks}
        return cls(**data)

    def register(self, app: Celery, app_registry: TaskRegistry):
        for task in self.values():
            app_registry.register(task)
            app.register_task(task)
