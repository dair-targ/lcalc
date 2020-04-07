import functools
import logging

LOGGER = logging.getLogger('lcalc')
LOGGER.setLevel(logging.INFO)


def log(fn):
    if LOGGER.level > logging.DEBUG:
        return fn

    def log_result(self, args, kwargs, result):
        LOGGER.debug('%s --%s.%s(%s)--> %s' % (
            self,
            self.__class__.__name__,
            fn.__name__,
            ','.join(map(str, list(args) + ['%s=%s' % (k, v) for k, v in kwargs.items()])),
            result
        ))

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        log_result(self, args, kwargs, '...')
        result = fn.__call__(self, *args, **kwargs)
        log_result(self, args, kwargs, result)
        return result
    return wrapper
