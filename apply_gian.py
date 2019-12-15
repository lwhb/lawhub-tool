#!/usr/bin/env python3

import argparse
import json
import logging
import sys
import xml.etree.ElementTree as ET

from lawhub.action import Action, ActionType
from lawhub.law import parse
from lawhub.query import Query, QueryType
from lawhub.util import StatsFactory

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


def apply_replace(action, query2node):
    if action.at not in query2node:
        LOGGER.warning(f'failed to locate {action.at}')
        return False
    node = query2node[action.at]
    if not (hasattr(node, 'sentence')) or action.old not in node.sentence:
        LOGGER.warning(f'\"{action.old}\" does not exist in {action.at}')
        return False
    node.sentence = node.sentence.replace(action.old, action.new)
    LOGGER.debug(f'replaced \"{action.old}\" in {action.at} to \"{action.new}\"')
    return True


def apply_add(action, query2node):
    if action.at.query_type != QueryType.AFTER_WORD:
        return False  # ToDo: implement other QueryType
    if action.at not in query2node:
        LOGGER.warning(f'failed to locate {action.at}')
        return False
    node = query2node[action.at]
    if not (hasattr(node, 'sentence')) or action.at.word not in node.sentence:
        LOGGER.warning(f'\"{action.at.word}\" does not exist in {action.at}')
        return False
    idx = node.sentence.find(action.at.word)
    node.sentence = node.sentence[:idx] + action.what + node.sentence[idx:]
    LOGGER.debug(f'added \"{action.what}\" at {action.at}')
    return True


def is_target_action(action):
    if action.action_type == ActionType.REPLACE:
        return True
    if action.action_type == ActionType.ADD:
        if action.at.query_type == QueryType.AFTER_WORD:
            return True
    return False


def apply_gian(gian_fp, query2node, stats_factory):
    applied_actions = []
    process_count = 0
    success_count = 0
    with open(gian_fp, 'r') as f:
        for line in f:
            if line[:2] == '!!' or line[:2] == '//':
                continue
            action = Action(json.loads(line))
            if is_target_action(action):
                process_count += 1
                if action.action_type == ActionType.REPLACE:
                    success = apply_replace(action, query2node)
                elif action.action_type == ActionType.ADD:
                    success = apply_add(action, query2node)
                success_count += int(success)
            else:
                pass  # ToDo: implement other ActionType
    stats_factory.add({'file': gian_fp, 'process': process_count, 'success': success_count})
    return applied_actions


def main(law_fp, gian_fp, out_fp, stat_fp, applied_fp):
    LOGGER.info(f'Start to parse {law_fp}')
    try:
        tree = ET.parse(law_fp)
        nodes = [parse(node) for node in tree.getroot()]
        query2node = build_query2node(nodes)
    except Exception as e:
        msg = f'failed to parse {law_fp}: {e}'
        LOGGER.error(msg)
        sys.exit(1)

    if gian_fp:
        LOGGER.info(f'Start to apply {gian_fp}')
        stats_factory = StatsFactory(['file', 'process', 'success'])
        applied_actions = apply_gian(gian_fp, query2node, stats_factory)
        stat = stats_factory.get_last()
        LOGGER.info('Applied {} / {} actions'.format(stat['success'], stat['process']))

        if stat_fp:
            stats_factory.commit(stat_fp)
            LOGGER.info(f'Appended stats to {stat_fp}')

        if applied_fp:
            with open(applied_fp, 'w') as f:
                for action in applied_actions:
                    f.write(json.dumps(action.to_dict(), ensure_ascii=False) + '\n')
            LOGGER.info(f'Saved applied actions to {applied_fp}')

    with open(out_fp, 'w') as f:
        for node in nodes:
            f.write(f'{node}\n')
    LOGGER.info(f'Saved result to {out_fp}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='法律ファイル（.xml）及び議案ファイル（.jsonl)を受け取り、改正した法律をTXT形式で出力する')
    parser.add_argument('-l', '--law', help='法律ファイル(.xml)', required=True)
    parser.add_argument('-g', '--gian', help='議案ファイル(.jsonl). 指定しない場合は改正せずに出力')
    parser.add_argument('-o', '--out', help='出力ファイル(.txt)', required=True)
    parser.add_argument('-s', '--stat', help='処理結果を保存する')
    parser.add_argument('-a', '--applied', help='適用されたActionを保存する')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    main(args.law, args.gian, args.out, args.stat, args.applied)
