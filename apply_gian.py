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
    LOGGER.info(f"Trying to parse {law_fp}")
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
                LOGGER.debug(f'duplicated query({query}) for {type(node)}')
            else:
                query2node[query] = node
        for child in node.children[::-1]:
            stack.append((child, title))

    process_count = 0
    success_count = 0
    LOGGER.info(f"Start to process {gian_fp}")
    with open(gian_fp, 'r') as f:
        for line in f:
            if line[:2] == '!!' or line[:2] == '//':
                continue
            process_count += 1
            action = Action(json.loads(line))
            if action.action_type == ActionType.REPLACE:
                if action.at in query2node:
                    node = query2node[action.at]
                    if not(hasattr(node, 'sentence')) or action.old not in node.sentence:
                        LOGGER.error(f'\"{action.old}\" does not exist in \"{action.at}\"')
                        continue
                    node.sentence = node.sentence.replace(action.old, action.new)
                    LOGGER.debug(f'Replaced \"{action.old}\" in {action.at} to \"{action.new}\"')
                    success_count += 1
                else:
                    LOGGER.error(f'failed to locate \"{action.at}\"')
    LOGGER.info(f'Successfully parsed {success_count} / {process_count} lines')

    with open(out_fp, 'w') as f:
        for node in nodes:
            f.write(f'{node}\n')
    LOGGER.info(f'Saved {out_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, datefmt="%m/%d/%Y %I:%M:%S",
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
