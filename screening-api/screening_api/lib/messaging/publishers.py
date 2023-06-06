"""Screening API lib messaging publishers module"""
import json
import logging

from kombu.pools import Connections
from kombu.utils.uuid import uuid

from screening_api.lib.messaging.utils import get_origin

log = logging.getLogger(__name__)


class CeleryTaskPublisher:

    lang = 'py'
    content_type = 'application/json'
    content_encoding = 'utf-8'
    serializer = 'json'

    def __init__(self, broker, routing_key, connections_limit=0):
        self.broker = broker
        self.routing_key = routing_key
        self.connections_pool = Connections(limit=connections_limit)

    def publish(self, name, *args, **kwargs):
        log.debug("Publishing {0} task (args:{1}, kwargs:{2})".format(
            name, args, kwargs))
        task_id = uuid()
        message = json.dumps((args, kwargs, None))
        headers = self.get_headers(task_id, name, args, kwargs)
        properties = self.get_properties(task_id)
        self.producer.publish(message, headers=headers, **properties)

    def publish_many(self, data_list):
        for data in data_list:
            self.publish(data)

    @property
    def producer(self):
        with self.connections_pool[self.broker].acquire() as connection:
            return connection.Producer(
                serializer=self.serializer, routing_key=self.routing_key)

    def get_headers(self, task_id, name, args, kwargs):
        return {
            'id': task_id,
            'lang': self.lang,
            'task': name,
            'argsrepr': repr(args),
            'kwargsrepr': repr(kwargs),
            'origin': get_origin(),
        }

    def get_properties(self, task_id):
        return {
            'correlation_id': task_id,
            'content_type': self.content_type,
            'content_encoding': self.content_encoding,
        }
