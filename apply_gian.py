#!/usr/bin/env python3

"""
法律ファイル（.xml）及び議案ファイル（.jsonl)を受け取り、改正した法律をTXT形式で出力する
"""

import json
import logging
import sys
import xml.etree.ElementTree as ET

from lawhub.action import Action, ActionType
from lawhub.law import parse
from lawhub.query import Query

LOGGER = logging.getLogger('apply_gian')


def build_query2node(nodes):
    query2node = dict()
    stack = [(node, '') for node in nodes]
    while len(stack) > 0:
        node, upper_title = stack.pop()
        title = upper_title + node.get_title()
        try:
            query = Query(title)
        except Exception as e:
            LOGGER.debug(e)
        else:
            if not (query.is_empty()) and node.get_title() != '':
                if query in query2node:
                    LOGGER.debug(f'duplicated query({query}) for {type(node)}')
                else:
                    query2node[query] = node
        for child in node.children[::-1]:
            stack.append((child, title))
    return query2node


def main(law_fp, gian_fp, out_fp):
    LOGGER.info(f'Start to parse {law_fp}')
    tree = ET.parse(law_fp)
    nodes = [parse(node) for node in tree.getroot()]
    query2node = build_query2node(nodes)

    process_count = 0
    success_count = 0
    LOGGER.info(f'Start to process {gian_fp}')
    with open(gian_fp, 'r') as f:
        for line in f:
            if line[:2] == '!!' or line[:2] == '//':
                continue
            action = Action(json.loads(line))
            if action.action_type == ActionType.REPLACE:
                process_count += 1
                if action.at not in query2node:
                    LOGGER.error(f'failed to locate \"{action.at}\"')
                    continue
                node = query2node[action.at]
                if not (hasattr(node, 'sentence')) or action.old not in node.sentence:
                    LOGGER.error(f'\"{action.old}\" does not exist in \"{action.at}\"')
                    continue
                node.sentence = node.sentence.replace(action.old, action.new)
                LOGGER.debug(f'replaced \"{action.old}\" in {action.at} to \"{action.new}\"')
                success_count += 1
    LOGGER.info(f'Successfully applied {success_count} / {process_count} actions')

    with open(out_fp, 'w') as f:
        for node in nodes:
            f.write(f'{node}\n')
    LOGGER.info(f'Saved {out_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, datefmt="%m/%d/%Y %I:%M:%S",
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
