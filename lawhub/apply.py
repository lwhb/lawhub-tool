from logging import getLogger

from lawhub.action import ReplaceAction, AddWordAction, DeleteAction
from lawhub.law import LawNodeFinder

LOGGER = getLogger(__name__)


class NodeNotFoundError(Exception):
    def __init__(self, query):
        self.query = query

    def __str__(self):
        return f'failed to locate {self.query}'


class TextNotFoundError(Exception):
    def __init__(self, text, query):
        self.text = text
        self.query = query

    def __str__(self):
        return f'"{self.text}" does not exist in {self.query}'


class MultipleTextFoundError(Exception):
    def __init__(self, text, query):
        self.text = text
        self.query = query

    def __str__(self):
        return f'found "{self.text}" multiple times in {self.query.text}'


def apply_replace(action, node_finder):
    assert isinstance(action, ReplaceAction)
    assert isinstance(node_finder, LawNodeFinder)

    try:
        node = node_finder.find(action.at)[0]
    except Exception as e:
        raise NodeNotFoundError(action.at) from e
    if not (hasattr(node, 'sentence')) or action.old not in node.sentence:
        raise TextNotFoundError(action.old, action.at)
    if node.sentence.count(action.old) > 1:
        raise MultipleTextFoundError(action.old, action.at)
    node.sentence = node.sentence.replace(action.old, action.new)
    LOGGER.debug(f'replaced \"{action.old}\" in {action.at} to \"{action.new}\"')


def apply_add_word(action, node_finder):
    assert isinstance(action, AddWordAction)
    assert isinstance(node_finder, LawNodeFinder)

    try:
        node = node_finder.find(action.at)[0]
    except Exception as e:
        raise NodeNotFoundError(action.at) from e
    if not (hasattr(node, 'sentence')) or action.word not in node.sentence:
        raise TextNotFoundError(action.word, action.at)
    if node.sentence.count(action.word) > 1:
        raise MultipleTextFoundError(action.word, action.at)
    idx = node.sentence.find(action.word) + len(action.word)
    node.sentence = node.sentence[:idx] + action.what + node.sentence[idx:]
    LOGGER.debug(f'added \"{action.what}\" at {action.at}')


def apply_delete(action, node_finder):
    assert isinstance(action, DeleteAction)
    assert isinstance(node_finder, LawNodeFinder)

    try:
        node = node_finder.find(action.at)[0]
    except Exception as e:
        raise NodeNotFoundError(action.at) from e
    if not (hasattr(node, 'sentence')):
        raise TextNotFoundError('', action.at)
    for what in action.whats:
        count = node.sentence.count(what)
        if count == 0:
            raise TextNotFoundError(what, action.at)
        elif count > 1:
            raise MultipleTextFoundError(what, action.at)
    for what in action.whats:
        node.sentence = node.sentence.replace(what, '')
        LOGGER.debug(f'deleted \"{what}\" in {action.at}')
