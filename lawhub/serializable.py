"""
Serializable class from Effective Python (section 26 and 34)
"""

import json
from enum import Enum
from logging import getLogger

LOGGER = getLogger(__name__)


class ToDictMixin(object):
    def to_dict(self):
        return self._traverse_dict(self.__dict__)

    def _traverse_dict(self, instance_dict):
        output = {}
        for key, value in instance_dict.items():
            output[key] = self._traverse(key, value)
        return output

    def _traverse(self, key, value):
        if isinstance(value, ToDictMixin):
            return value.to_dict()
        elif isinstance(value, dict):
            return self._traverse_dict(value)
        elif isinstance(value, list) or isinstance(value, tuple):
            return [self._traverse(key, i) for i in value]
        elif isinstance(value, Enum):
            return value.value
        elif hasattr(value, '__dict__'):
            return self._traverse_dict(value.__dict__)
        else:
            return value


class Registry(type):
    registry = {}

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        Registry.registry[cls.__name__] = cls
        return cls


class Serializable(ToDictMixin, metaclass=Registry):
    """
    All attributes need to have corresponding arguments in constructor with the same name
    """

    def to_dict(self):
        return self._traverse_dict({
            '__class__': self.__class__.__name__,
            '__dict__': self.__dict__
        })

    def serialize(self):
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, params):
        if isinstance(params, dict) and '__class__' in params and '__dict__' in params:
            if params['__class__'] not in Registry.registry:
                LOGGER.warning('Unsupported Serializable class found: ' + params['__class__'])
                return params
            target_class = Registry.registry[params['__class__']]
            kwargs = {}
            for key, val in params['__dict__'].items():
                kwargs[key] = cls.from_dict(val)
            return target_class(**kwargs)
        if isinstance(params, list):
            return [cls.from_dict(v) for v in params]
        else:
            return params

    @classmethod
    def deserialize(cls, data):
        # noinspection PyUnresolvedReferences
        import lawhub.action, lawhub.query, lawhub.law  # update Registry
        return cls.from_dict(json.loads(data))


def is_serializable(obj):
    return obj == Serializable.deserialize(obj.serialize())
