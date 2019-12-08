#!/usr/bin/env python3

import argparse
import json
import logging
import re
import sys
from pathlib import Path

from lawhub.action import Action, ActionType
from lawhub.nlp import split_with_escape, normalize_last_verb
from lawhub.query import QueryCompensator
from lawhub.util import StatsFactory

LOGGER = logging.getLogger('parse_gian')


def split_to_chunks(lines):
    """
    議案を1改正文=1チャンクになるように分割する
    :param lines: list of string
    :return: list of chunks (=list of string)
    """

    kaisei_idxs = []
    for idx, line in enumerate(lines):
        if '次のように改正する' in line:
            kaisei_idxs.append(idx)
    LOGGER.debug(f'Found {len(kaisei_idxs)} kaisei lines')

    chunks = []
    if len(kaisei_idxs) <= 1:
        chunks.append(lines)
    else:
        start_idx = 0
        for idx in kaisei_idxs[1:]:
            pattern = r'（.*）'  # check if Article caption
            match = re.match(pattern, lines[idx - 1])
            end_idx = idx - 1 if match else idx  # excludes next Article caption
            chunks.append(lines[start_idx:end_idx])
            start_idx = end_idx
        chunks.append(lines[start_idx:])
    return chunks


def parse_actions(line):
    """
    :param line:
    :return:
        1. list of actions, even if partial success
        2. success flag if whole line is successfully converted to actions
    """

    actions = []
    process_count = 0
    success_count = 0

    qc = QueryCompensator()
    for text in split_with_escape(line.strip()):
        process_count += 1
        try:
            action = Action(normalize_last_verb(text))
            if action.action_type in (ActionType.ADD, ActionType.DELETE, ActionType.REPLACE):
                action.at = qc.compensate(action.at)
            elif action.action_type == ActionType.RENAME:
                action.old = qc.compensate(action.old)
                action.new = qc.compensate(action.new)
            actions.append(action)
            success_count += 1
        except ValueError as e:
            pass

    return actions, process_count, success_count


def main(in_fp, stat_fp):
    try:
        with open(in_fp, 'r') as f:
            data = json.load(f)
            lines = data['main'].split('\n')
            chunks = split_to_chunks(lines)
    except Exception as e:
        msg = f'Failed to load GIAN from {in_fp}'
        LOGGER.error(msg)
        sys.exit(1)
    LOGGER.info(f'Loaded {len(lines)} lines ({len(chunks)} chunks) from {in_fp}')

    stats_factory = StatsFactory(['file', 'process', 'success'])
    for chunk_id, chunk in enumerate(chunks):
        out_fp = in_fp.parent / f'{chunk_id}.jsonl'
        with open(out_fp, 'w') as f:
            process_count = 0
            success_count = 0
            for line in chunk:
                f.write(f'!!{line}\n')
                if ('　' in line) or (len(line) > 0 and line[0] == '（'):
                    pass  # AdHoc fix to skip likely law sentence
                else:
                    actions, pc, sc = parse_actions(line)
                    for action in actions:  # output actions even if partial success (ISSUE14)
                        f.write(f'{json.dumps(action.to_dict(), ensure_ascii=False)}\n')
                    process_count += pc
                    success_count += sc
        LOGGER.info(f'Successfully parsed {success_count} / {process_count} segments')
        stats_factory.add({'file': out_fp, 'process': process_count, 'success': success_count})
        LOGGER.info(f'Saved {out_fp}')
    stats_factory.commit(stat_fp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='議案ファイル（.json)を受け取り、パースした結果を法案ごとに分けてJSON Lines形式（1.jsonl, 2.jsonl, ...）で保存する')
    parser.add_argument('-g', '--gian', help='議案ファイル(.json)', required=True)
    parser.add_argument('-s', '--stat')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    main(Path(args.gian), args.stat)
