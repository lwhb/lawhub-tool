#!/usr/bin/env python3

import sys
import json
import logging
import xml.etree.ElementTree as ET

from lawhub.action import Action, ActionType
from lawhub.law import parse
from lawhub.query import Query

LOGGER = logging.getLogger(__name__)


def main(law_fp, gian_fp, out_fp):
    tree = ET.parse(law_fp)
    nodes = [parse(node) for node in tree.getroot()]

    query2node = dict()
    stack = [(node, '') for node in nodes]
    while len(stack) > 0:
        node, upper_title = stack.pop()
        title = upper_title + node.get_title()
        query = Query(title)
        if not (query.is_empty()) and node.get_title() != '':
            if query in query2node:
                print(f'duplicated query({query}) for {type(node)}')
            else:
                query2node[query] = node
        for child in node.children[::-1]:
            stack.append((child, title))

    with open(gian_fp, 'r') as f:
        for line in f:
            if line[:2] == '!!' or line[:2] == '//':
                continue
            action = Action(json.loads(line))
            if action.action_type == ActionType.REPLACE:
                if action.at in query2node:
                    node = query2node[action.at]
                    if action.old in node.sentence:
                        node.sentence = node.sentence.replace(action.old, action.new)
                        LOGGER.debug(f'Replaced \"{action.old}\" in {action.at} to \"{action.new}\"')
                    else:
                        LOGGER.error(f'\"{action.old}\" does not exist in \"{action.at}\"')
                else:
                    LOGGER.error(f'Failed to locate \"{action.at}\"')

    with open(out_fp, 'w') as f:
        for node in nodes:
            f.write(f'{node}\n')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, datefmt="%m/%d/%Y %I:%M:%S",
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
