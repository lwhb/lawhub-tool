#!/usr/bin/env python3

"""
議案ファイル（.json)を受け取り、mainをパースした結果をJSON Lines形式で保存する

ToDo: 複数の法律を改正している場合に対応するため、一つのファイルではなく複数のファイルに出力する様にする (ISSUE-3)
"""

import json
import logging
import sys

from lawhub.action import Action, ActionType
from lawhub.nlp import split_with_escape, normalize_last_verb
from lawhub.query import QueryCompensator

LOGGER = logging.getLogger('parse_gian')


def main(in_fp, out_fp):
    with open(in_fp, 'r') as f:
        data = json.load(f)
    LOGGER.info(f'Loaded {in_fp}')

    process_count = 0
    success_count = 0
    with open(out_fp, 'w') as f:
        for line in data['main'].split('\n'):
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
    LOGGER.info(f'Successfully parsed {success_count} / {process_count} lines')
    LOGGER.info(f'Saved {out_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, datefmt="%m/%d/%Y %I:%M:%S",
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main(sys.argv[1], sys.argv[2])
