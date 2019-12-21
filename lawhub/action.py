import re
from enum import Enum
from logging import getLogger

from lawhub.nlp import normalize_last_verb, mask_escape
from lawhub.query import Query, QueryType

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

    def __init__(self, obj, meta=None):
        if isinstance(obj, dict):
            self.__init_by_dict__(obj)
        elif isinstance(obj, str):
            self.__init_by_str__(obj, meta)
        else:
            msg = f'Failed to instantiate Action from {type(obj)}'
            raise NotImplementedError(msg)

    def __init_by_dict__(self, data):
        try:
            self.text = data['text']
            self.meta = data['meta']
            self.action_type = ActionType(data['action_type'])
            if self.action_type == ActionType.ADD:
                self.at = Query(data['at'])
                self.what = data['what']
            elif self.action_type == ActionType.DELETE:
                self.at = Query(data['at'])
                self.whats = data['whats']
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

    def __init_by_str__(self, text, meta=None):
        self.text = text
        self.meta = dict()
        if meta:
            self.meta.update(meta)

        norm_text = normalize_last_verb(self.text)
        if self.__init_add__(norm_text):
            self.action_type = ActionType.ADD
        elif self.__init_delete__(norm_text):
            self.action_type = ActionType.DELETE
        elif self.__init_replace__(norm_text):
            self.action_type = ActionType.REPLACE
        elif self.__init_rename__(norm_text):
            self.action_type = ActionType.RENAME
        else:
            msg = f'failed to instantiate Action from text="{text}"'
            raise ValueError(msg)

    def __init_add__(self, text):
        pattern = r'(.*)に(.*)を加える'
        masked_text, placeholder_map = mask_escape(text)
        match = re.match(pattern, masked_text)
        if match:
            self.at = Query(match.group(1).format(**placeholder_map))
            self.what = match.group(2).format(**placeholder_map)
            if self.at.query_type == QueryType.AFTER_WORD:
                if len(self.what) > 2 and self.what[0] == '「' and self.what[-1] == '」':
                    self.what = self.what[1:-1]
                    return True
            else:
                return True
        return False

    def __init_delete__(self, text):
        pattern = r'(.*)中「(.*)」を削る'
        match = re.match(pattern, text)
        if match:
            self.at = Query(match.group(1))
            self.whats = match.group(2).split('」及び「')
            return True
        return False

    def __init_replace__(self, text):
        pattern = r'(.*)中「(.*)」を「(.*)」に改める'
        match = re.match(pattern, text)
        if match:
            self.at = Query(match.group(1))
            self.old = match.group(2)
            self.new = match.group(3)
            return True
        return False

    def __init_rename__(self, text):
        pattern = r'(.*)を(.*)とする'
        match = re.match(pattern, text)
        if match:
            self.old = Query(match.group(1))
            self.new = Query(match.group(2))
            return True
        return False

    def to_dict(self):
        data = {
            'action_type': self.action_type.value,
            'text': self.text,
            'meta': self.meta
        }
        if self.action_type == ActionType.ADD:
            data['at'] = self.at.to_dict()
            data['what'] = self.what
        elif self.action_type == ActionType.DELETE:
            data['at'] = self.at.to_dict()
            data['whats'] = self.whats
        elif self.action_type == ActionType.REPLACE:
            data['at'] = self.at.to_dict()
            data['old'] = self.old
            data['new'] = self.new
        elif self.action_type == ActionType.RENAME:
            data['old'] = self.old.to_dict()
            data['new'] = self.new.to_dict()
        else:
            msg = f'unknown ActionType={self.action_type}'
            raise NotImplementedError(msg)
        return data

    def __repr__(self):
        if self.action_type == ActionType.ADD:
            return f'<ADD at={self.at.text} what={self.what}>'
        elif self.action_type == ActionType.DELETE:
            return f'<DELETE at={self.at.text} whats={self.whats}>'
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
            return self.at == other.at and self.whats == other.whats
        elif self.action_type == ActionType.REPLACE:
            return self.at == other.at and self.old == other.old and self.new == other.old
        elif self.action_type == ActionType.RENAME:
            return self.old == other.old and self.new == other.old
        else:
            msg = f'unknown ActionType={self.action_type}'
            raise NotImplementedError(msg)
