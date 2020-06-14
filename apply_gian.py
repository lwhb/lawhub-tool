#!/usr/bin/env python3

import argparse
import json
import logging
import sys

from lawhub.action import ReplaceAction, AddWordAction, DeleteAction
from lawhub.apply import apply_replace, apply_add_word, apply_delete
from lawhub.constants import LOG_DATE_FORMAT, LOG_FORMAT
from lawhub.law import LawNodeFinder, LawHierarchy, parse_xml_fp, extract_law_meta, save_law_tree
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
                    applied_actions.append(action)
                except Exception as e:
                    LOGGER.debug(e)
                    failed_actions.append(action)
            else:
                skipped_actions.append(action)
    return applied_actions, failed_actions, skipped_actions


def main(law_fp, gian_fp, out_fp, stat_fp, applied_fp, failed_fp, skipped_fp):
    LOGGER.info(f'Start to parse {law_fp}')
    try:
        meta = extract_law_meta(law_fp)
        nodes = parse_xml_fp(law_fp)
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

    save_law_tree(meta['LawTitle'], nodes, out_fp)
    LOGGER.info(f'Saved result to {out_fp}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JSON Lines形式にパースされた議案ファイル（.jsonl)および改正対象の法律ファイル（.xml）を受け取り、改正した法律をTXT形式で出力する')
    parser.add_argument('-g', '--gian', help='議案ファイル(.jsonl). 指定しない場合は改正せずに出力')
    parser.add_argument('-l', '--law', help='法律ファイル(.xml)', required=True)
    parser.add_argument('-o', '--out', help='出力ファイル(.txt)', required=True)
    parser.add_argument('--applied', help='適用されたActionを保存する')
    parser.add_argument('--failed', help='適用されなかったActionを保存する')
    parser.add_argument('--skipped', help='飛ばされたActionを保存する')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-s', '--stat')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, datefmt=LOG_DATE_FORMAT, format=LOG_FORMAT)

    main(args.law, args.gian, args.out, args.stat, args.applied, args.failed, args.skipped)
