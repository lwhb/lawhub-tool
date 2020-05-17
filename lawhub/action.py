"""
法改正のActionを表現するクラスを定義する
"""

import re
from logging import getLogger

from lawhub.nlp import mask_escape, normalize_last_verb, split_with_escape
from lawhub.query import Query, QueryCompensator
from lawhub.serializable import Serializable

LOGGER = getLogger(__name__)


def line_to_action_nodes(line, meta=None):
    """
    :param line:
    :param meta: any metadata in key-value form
    :return:
        1. list of actions, even if partial success
        2. success/process count metrics
    """

    actions = []
    process_count = 0
    success_count = 0

    qc = QueryCompensator()
    for text in split_with_escape(line.strip()):
        process_count += 1
        try:
            action = parse_action_text(text, meta)
            if isinstance(action, (AddWordAction, AddLawAction, DeleteAction, ReplaceAction)):
                action.at = qc.compensate(action.at)
            elif isinstance(action, RenameAction):
                action.old = qc.compensate(action.old)
                action.new = qc.compensate(action.new)
            actions.append(action)
            success_count += 1
        except ValueError as e:
            LOGGER.debug(e)

    return actions, process_count, success_count


def parse_action_text(text, meta=None):
    for cls in [AddWordAction,
                AddLawAction,
                DeleteAction,
                ReplaceAction,
                RenameAction]:
        try:
            return cls.from_text(text, meta)
        except ValueError:
            pass
    raise ValueError(f'failed to instantiate Action from "{text}"')


class AbstractAction(Serializable):
    pattern = r'NotImplemented'

    def __init__(self, text, meta=None):
        self.text = text
        self.meta = meta

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.text}>'

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @classmethod
    def _match_pattern(cls, text):
        norm_text = normalize_last_verb(text)
        match = re.match(cls.pattern, norm_text)
        if not match:
            msg = f'input text "{norm_text}" does not match "{cls.pattern}"'
            raise ValueError(msg)
        return match

    @classmethod
    def from_text(cls, text, meta=None):
        raise NotImplemented


class AddWordAction(AbstractAction):
    pattern = r'(?:([^「」]*)中)?「(.*)」の下に「(.*)」を(加える)?'


    def __init__(self, text, meta, at, word, what):
        super().__init__(text, meta)
        self.at = at
        self.word = word
        self.what = what

    @classmethod
    def from_text(cls, text, meta=None):
        match = cls._match_pattern(text)
        return cls(text=text,
                   meta=meta,
                   at=Query.from_text(match.group(1)),
                   word=match.group(2),
                   what=match.group(3))


class AddLawAction(AbstractAction):
    pattern = r'(.*)に次の(.*)を加える'

    def __init__(self, text, meta, at, what, law=None):
        super().__init__(text, meta)
        self.at = at
        self.what = what
        self.law = law

    @classmethod
    def from_text(cls, text, meta=None):
        masked_text, placeholder_map = mask_escape(text)
        match = cls._match_pattern(masked_text)
        return cls(text=text,
                   meta=meta,
                   at=Query.from_text(match.group(1).format(**placeholder_map)),
                   what=match.group(2).format(**placeholder_map))


class DeleteAction(AbstractAction):
    pattern = r'(?:([^「」]*)中)?「(.*)」を削る'

    def __init__(self, text, meta, at, whats):
        super().__init__(text, meta)
        self.at = at
        self.whats = whats

    @classmethod
    def from_text(cls, text, meta=None):
        match = cls._match_pattern(text)
        return cls(text=text,
                   meta=meta,
                   at=Query.from_text(match.group(1)),
                   whats=match.group(2).split('」及び「'))


class ReplaceAction(AbstractAction):
    pattern = r'(?:([^「」]*)中)?「(.*)」を「(.*)」に(改める)?'

    def __init__(self, text, meta, at, old, new):
        super().__init__(text, meta)
        self.at = at
        self.old = old
        self.new = new

    @classmethod
    def from_text(cls, text, meta=None):
        match = cls._match_pattern(text)
        return cls(text=text,
                   meta=meta,
                   at=Query.from_text(match.group(1)),
                   old=match.group(2),
                   new=match.group(3))


class RenameAction(AbstractAction):
    pattern = r'(.*)を(.*)とする'

    def __init__(self, text, meta, old, new):
        super().__init__(text, meta)
        self.old = old
        self.new = new

    @classmethod
    def from_text(cls, text, meta=None):
        match = cls._match_pattern(text)
        return cls(text=text,
                   meta=meta,
                   old=Query.from_text(match.group(1)),
                   new=Query.from_text(match.group(2)))
