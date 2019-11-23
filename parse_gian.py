#!/usr/bin/env python3

import json
import logging

from lawhub.action import Action, ActionType
from lawhub.nlp import split_with_escape, normalize_last_verb
from lawhub.query import QueryCompensator

LOGGER = logging.getLogger(__name__)


def main(in_fp, out_fp):
    with open(in_fp, 'r') as f:
        data = json.load(f)

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
                    f.write(f'{action.to_dict()}\n')
                success_count += 1
    LOGGER.info(f'Successfully parsed {success_count} / {process_count} lines')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, datefmt="%m/%d/%Y %I:%M:%S",
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    in_fp = '/Users/musui/lawhub/lawhub-spider/data/syuhou/195/4/houan.json'
    out_fp = 'out.jsonl'
    main(in_fp, out_fp)
