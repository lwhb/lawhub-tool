#!/usr/bin/env python3

import argparse
import json
import logging
import sys
import xml.etree.ElementTree as ET

from lawhub.action import ReplaceAction, AddWordAction, DeleteAction
from lawhub.apply import apply_replace, apply_add_word, apply_delete
from lawhub.law import parse_xml, LawNodeFinder, LawHierarchy
from lawhub.serializable import Serializable
from lawhub.util import StatsFactory

LOGGER = logging.getLogger('apply_gian')


def is_target_action(action):
    return isinstance(action, (ReplaceAction, AddWordAction, DeleteAction))


def is_target_query(query):
    for hrchy in [LawHierarchy.SUPPLEMENT, LawHierarchy.CONTENTS, LawHierarchy.TABLE]:
        if query.has(hrchy):
            return False
    return True


def apply_gian(gian_fp, node_finder):
    applied_actions = []
    failed_actions = []
    skipped_actions = []
    with open(gian_fp, 'r') as f:
        for line in f:
            if line[:2] == '!!' or line[:2] == '//':
                continue
            action = Serializable.deserialize(line)
            if is_target_action(action) and is_target_query(action.at):
                try:
                    if isinstance(action, ReplaceAction):
                        apply_replace(action, node_finder)
                    elif isinstance(action, AddWordAction):
                        apply_add_word(action, node_finder)
                    elif isinstance(action, DeleteAction):
                        apply_delete(action, node_finder)
                except Exception as e:
                    LOGGER.debug(e)
                    failed_actions.append(action)
                else:
                    applied_actions.append(action)
    return applied_actions, failed_actions, skipped_actions


def main(law_fp, gian_fp, out_fp, stat_fp, applied_fp, failed_fp, skipped_fp):
    LOGGER.info(f'Start to parse {law_fp}')
    try:
        tree = ET.parse(law_fp)
        nodes = [parse_xml(node) for node in tree.getroot()]
    except Exception as e:
        msg = f'failed to parse {law_fp}: {e}'
        LOGGER.error(msg)
        sys.exit(1)
    node_finder = LawNodeFinder(nodes)

    if gian_fp:
        LOGGER.info(f'Start to apply {gian_fp}')
        stats_factory = StatsFactory(['file', 'process', 'success'])
        applied_actions, failed_actions, skipped_actions = apply_gian(gian_fp, node_finder)
        process_count = len(applied_actions) + len(failed_actions)
        success_count = len(applied_actions)
        stats_factory.add({'file': gian_fp, 'process': process_count, 'success': success_count})
        LOGGER.info('Applied {} / {} actions'.format(success_count, process_count))

        if stat_fp:
            stats_factory.commit(stat_fp)
            LOGGER.info(f'Appended stats to {stat_fp}')

        if applied_fp:
            with open(applied_fp, 'w') as f:
                for action in applied_actions:
                    f.write(json.dumps(action.to_dict(), ensure_ascii=False) + '\n')
            LOGGER.info(f'Saved applied actions to {applied_fp}')

        if failed_fp:
            with open(failed_fp, 'w') as f:
                for action in failed_actions:
                    f.write(json.dumps(action.to_dict(), ensure_ascii=False) + '\n')
            LOGGER.info(f'Saved failed actions to {failed_fp}')

        if skipped_fp:
            with open(skipped_fp, 'w') as f:
                for action in skipped_actions:
                    f.write(json.dumps(action.to_dict(), ensure_ascii=False) + '\n')
                LOGGER.info(f'Saved failed actions to {skipped_fp}')

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
    parser.add_argument('--applied', help='適用されたActionを保存する')
    parser.add_argument('--failed', help='適用できなかったActionを保存する')
    parser.add_argument('--skipped', help='飛ばされたActionを保存する')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    main(args.law, args.gian, args.out, args.stat, args.applied, args.failed, args.skipped)
