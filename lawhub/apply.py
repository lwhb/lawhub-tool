import logging

from lawhub.action import ActionType

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


class MultipleTextFoundError(Exception):
    def __init__(self, text, query):
        self.text = text
        self.query = query

    def __str__(self):
        return f'found {self.text} multiple times in {self.query}'


def apply_replace(action, query2node):
    if action.action_type != ActionType.REPLACE:
        raise ValueError(f'apply_replace() is called with invalid ActionType: {action.action_type}')
    if action.at not in query2node:
        raise NodeNotFoundError(action.at)
    node = query2node[action.at]
    if not (hasattr(node, 'sentence')) or action.old not in node.sentence:
        raise TextNotFoundError(action.old, action.at)
    if node.sentence.count(action.old) > 1:
        raise MultipleTextFoundError(action.old, action.at)
    node.sentence = node.sentence.replace(action.old, action.new)
    LOGGER.debug(f'replaced \"{action.old}\" in {action.at} to \"{action.new}\"')


def apply_add_after(action, query2node):
    if action.action_type != ActionType.ADD_AFTER:
        raise ValueError(f'apply_add_after() is called with invalid ActionType: {action.action_type}')
    if action.at not in query2node:
        raise NodeNotFoundError(action.at)
    node = query2node[action.at]
    if not (hasattr(node, 'sentence')) or action.word not in node.sentence:
        raise TextNotFoundError(action.word, action.at)
    if node.sentence.count(action.word) > 1:
        raise MultipleTextFoundError(action.word, action.at)
    idx = node.sentence.find(action.word) + len(action.word)
    node.sentence = node.sentence[:idx] + action.what + node.sentence[idx:]
    LOGGER.debug(f'added \"{action.what}\" at {action.at}')


def apply_delete(action, query2node):
    if action.action_type != ActionType.DELETE:
        raise ValueError(f'apply_delete() is called with invalid ActionType: {action.action_type}')
    if action.at not in query2node:
        raise NodeNotFoundError(action.at)
    node = query2node[action.at]
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
