#!/usr/bin/env python3

"""
議案ファイル（.json)を受け取り、mainをパースした結果を同じディレクトリにJSON Lines形式（1.jsonl, 2.jsonl, ...）で保存する
"""

import json
import logging
import re
import sys
from pathlib import Path

from lawhub.action import Action, ActionType
from lawhub.nlp import split_with_escape, normalize_last_verb
from lawhub.query import QueryCompensator

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


def main(in_fp):
    with open(in_fp, 'r') as f:
        data = json.load(f)
        lines = data['main'].split('\n')
        chunks = split_to_chunks(lines)
    LOGGER.info(f'Loaded {len(lines)} lines ({len(chunks)} chunks) from {in_fp}')

    process_count = 0
    success_count = 0
    for chunk_id, chunk in enumerate(chunks):
        out_fp = in_fp.parent / f'{chunk_id}.jsonl'
        with open(out_fp, 'w') as f:
            for line in chunk:
                process_count += 1
                actions = []
                try:
                    qc = QueryCompensator()
                    for text in split_with_escape(line.strip()):
                        action = Action(normalize_last_verb(text))
                        if action.action_type in (ActionType.ADD, ActionType.DELETE, ActionType.REPLACE):
                            action.at = qc.compensate(action.at)
                        elif action.action_type == ActionType.RENAME:
                            action.old = qc.compensate(action.old)
                            action.new = qc.compensate(action.new)
                        actions.append(action)
                except Exception as e:
                    LOGGER.debug(f'failed to parse {line}: {e}')
                    f.write(f'!!{line}\n')
                else:
                    for action in actions:
                        f.write(f'{json.dumps(action.to_dict(), ensure_ascii=False)}\n')
                    success_count += 1
        LOGGER.info(f'Saved {out_fp}')
    LOGGER.info(f'Successfully parsed {success_count} / {process_count} lines')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, datefmt="%m/%d/%Y %I:%M:%S",
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main(Path(sys.argv[1]))
