import logging

from lawhub.query import QueryType

LOGGER = logging.getLogger(__name__)


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
        return f'{self.text} does not exist in {self.query}'


def apply_replace(action, query2node):
    if action.at not in query2node:
        raise NodeNotFoundError(action.at)
    node = query2node[action.at]
    if not (hasattr(node, 'sentence')) or action.old not in node.sentence:
        raise TextNotFoundError(action.old, action.at)
    node.sentence = node.sentence.replace(action.old, action.new)
    LOGGER.debug(f'replaced \"{action.old}\" in {action.at} to \"{action.new}\"')


def apply_add_after(action, query2node):
    if action.at.query_type != QueryType.AFTER_WORD:
        raise ValueError(f'apply_add_after() is called with invalid QueryType: {action.at.query_type}')
    if action.at not in query2node:
        raise NodeNotFoundError(action.at)
    node = query2node[action.at]
    if not (hasattr(node, 'sentence')) or action.at.word not in node.sentence:
        raise TextNotFoundError(action.at.word, action.at)
    idx = node.sentence.find(action.at.word) + len(action.at.word)
    node.sentence = node.sentence[:idx] + action.what + node.sentence[idx:]
    LOGGER.debug(f'added \"{action.what}\" at {action.at}')


def apply_delete(action, query2node):
    if action.at not in query2node:
        raise NodeNotFoundError(action.at)
    node = query2node[action.at]
    if not (hasattr(node, 'sentence')) or action.what not in node.sentence:
        raise TextNotFoundError(action.old, action.what)
    node.sentence = node.sentence.replace(action.what, '')
    LOGGER.debug(f'deleted \"{action.what}\" in {action.at}')
