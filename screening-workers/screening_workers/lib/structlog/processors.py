class SentryProcessor(object):

    def __call__(self, wrapped_logger, method_name, event_dict):
        kwargs = dict(msg=event_dict.pop('event', None), extra=event_dict)
        if 'exception' in event_dict:
            kwargs['exc_info'] = True
        return kwargs
