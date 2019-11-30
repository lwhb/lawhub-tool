import re
from enum import Enum
from logging import getLogger

from lawhub.query import Query

LOGGER = getLogger(__name__)


class ActionType(str, Enum):
    ADD = 'add'
    DELETE = 'delete'
    REPLACE = 'replace'
    RENAME = 'rename'


class Action:
    """
    法改正のActionを表現するクラス
    """

    def __init__(self, obj):
        if isinstance(obj, dict):
            self.__init_by_dict__(obj)
        elif isinstance(obj, str):
            self.__init_by_str__(obj)
        else:
            msg = f'Failed to instantiate Action from {type(obj)}'
            raise NotImplementedError(msg)

    def __init_by_dict__(self, data):
        try:
            self.action_type = ActionType(data['action_type'])
            self.text = data['text']
            if self.action_type in (ActionType.ADD, ActionType.DELETE):
                self.at = Query(data['at'])
                self.what = data['what']
            elif self.action_type == ActionType.REPLACE:
                self.at = Query(data['at'])
                self.old = data['old']
                self.new = data['new']
            elif self.action_type == ActionType.RENAME:
                self.old = Query(data['old'])
                self.new = Query(data['new'])
            else:
                msg = 'unknown ActionType={self.action_type}'
                raise NotImplementedError(msg)
        except Exception as e:
            msg = f'Failed to instantiate Action from {data}: {e}'
            raise ValueError(msg)

    def __init_by_str__(self, text):
        self.text = text

        if self.__init_add__(text):
            self.action_type = ActionType.ADD
            return
        elif self.__init_delete__(text):
            self.action_type = ActionType.DELETE
            return
        elif self.__init_replace__(text):
            self.action_type = ActionType.REPLACE
            return
        elif self.__init_rename__(text):
            self.action_type = ActionType.RENAME
            return
        else:
            msg = f'failed to instantiate Action with text="{text}"'
            raise ValueError(msg)

    def __init_add__(self, text):
        pattern = r'(.*)に(.*)を加える'
        m = re.match(pattern, text)
        if m is None:
            return False
        else:
            self.at = Query(m.group(1))
            self.what = m.group(2)
            return True

    def __init_delete__(self, text):
        pattern = r'(.*)中「(.*)」を削る'
        m = re.match(pattern, text)
        if m is None:
            return False
        else:
            self.at = Query(m.group(1))
            self.what = m.group(2)
            return True

    def __init_replace__(self, text):
        pattern = r'(.*)中「(.*)」を「(.*)」に改める'
        m = re.match(pattern, text)
        if m is None:
            return False
        else:
            self.at = Query(m.group(1))
            self.old = m.group(2)
            self.new = m.group(3)
            return True

    def __init_rename__(self, text):
        pattern = r'(.*)を(.*)とする'
        m = re.match(pattern, text)
        if m is None:
            return False
        else:
            self.old = Query(m.group(1))
            self.new = Query(m.group(2))
            return True

    def to_dict(self):
        ret = {
            'action_type': self.action_type.value,
            'text': self.text
        }
        if self.action_type in (ActionType.ADD, ActionType.DELETE):
            ret['at'] = self.at.to_dict()
            ret['what'] = self.what
        elif self.action_type == ActionType.REPLACE:
            ret['at'] = self.at.to_dict()
            ret['old'] = self.old
            ret['new'] = self.new
        elif self.action_type == ActionType.RENAME:
            ret['old'] = self.old.to_dict()
            ret['new'] = self.new.to_dict()
        else:
            msg = f'unknown ActionType={self.action_type}'
            raise NotImplementedError(msg)
        return ret

    def __repr__(self):
        if self.action_type == ActionType.ADD:
            return f'<ADD at={self.at.text} what={self.what}>'
        elif self.action_type == ActionType.DELETE:
            return f'<DELETE at={self.at.text} what={self.what}>'
        elif self.action_type == ActionType.REPLACE:
            return f'<REPLACE at={self.at.text} old={self.old} new={self.new}>'
        elif self.action_type == ActionType.RENAME:
            return f'<RENAME old={self.old.text} new={self.new.text}>'
        else:
            msg = f'unknown ActionType={self.action_type}'
            raise NotImplementedError(msg)

    def __eq__(self, other):
        if not (isinstance(other, Action)):
            return False
        if self.action_type != other.action_type:
            return False
        if self.action_type == ActionType.ADD:
            return self.at == other.at and self.what == other.what
        elif self.action_type == ActionType.DELETE:
            return self.at == other.at and self.what == other.what
        elif self.action_type == ActionType.REPLACE:
            return self.at == other.at and self.old == other.old and self.new == other.old
        elif self.action_type == ActionType.RENAME:
            return self.old == other.old and self.new == other.old
        else:
            msg = f'unknown ActionType={self.action_type}'
            raise NotImplementedError(msg)
