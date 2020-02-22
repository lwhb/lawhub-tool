#!/usr/bin/env python3

import argparse
import json
import logging
import sys
from pathlib import Path

from lawhub.serializable import Serializable

LOGGER = logging.getLogger('apply_gian')


def create_replace_pairs(gian_fp, applied_fps):
    with open(gian_fp, 'r') as f:
        data = json.load(f)
        if 'main' not in data:
            raise ValueError(f'failed to find \'main\' in {gian_fp}')
        lines = data['main'].split('\n')
    LOGGER.debug(f'Loaded GIAN lines from {gian_fp}')

    idx2actions = {idx: [] for idx in range(len(lines))}
    for applied_fp in applied_fps:
        actions = [Serializable.deserialize(line) for line in open(applied_fp, 'r')]
        for action in actions:
            idx = action.meta['line']
            idx2actions[idx].append(action)
        LOGGER.debug(f'Loaded {len(actions)} Actions from {applied_fp}')

    pairs = []
    replace_count = 0
    for idx, line in enumerate(lines):
        new_line = line
        for action in idx2actions[idx]:
            count = new_line.count(action.text)
            if count == 0:
                LOGGER.warning(f'failed to find ActionText in JSON: {action.text}@{idx}')
                LOGGER.debug(new_line)
            elif count == 1:
                new_line = new_line.replace(action.text, '<strike>' + action.text + '</strike>')
                LOGGER.debug(f'stroked {action.text}@{idx}')
                replace_count += 1
            else:
                LOGGER.warning(f'found multiple occurrence of ActionText in JSON: {action.text}@{idx}')
                LOGGER.debug(new_line)
        pairs.append((line, new_line))
    LOGGER.debug(f'Configured {replace_count} replaces for {len(lines)} lines')
    return pairs


def create_new_html(html_fp, replace_pairs):
    with open(html_fp, 'r', encoding='shift-jis') as f:
        html = f.read()
        html = html.replace('shift_jis', 'utf-8')
        html = html.replace('−', '－')
        html = html.replace('&#22625;', '塡')
    LOGGER.debug(f'Loaded HTML from {html_fp}')

    new_html = ''
    prev_end = 0
    for (old_line, new_line) in replace_pairs:
        start = html.find(old_line, prev_end)
        if start == -1:
            LOGGER.warning(f'failed to find in HTML: {old_line}')
        else:
            new_html += (html[prev_end:start] + new_line)
            prev_end = start + len(old_line)
    new_html += html[prev_end:]

    return new_html


def main(gian_fp, in_fp, out_fp):
    gian_fp = Path(gian_fp)
    applied_fps = Path(gian_fp).parent.glob('*.applied')

    try:
        replace_pairs = create_replace_pairs(gian_fp, applied_fps)
        new_html = create_new_html(in_fp, replace_pairs)
    except Exception as e:
        msg = f'failed to visualize {gian_fp}: {e}'
        LOGGER.error(msg)
        sys.exit(1)

    with open(out_fp, 'w') as f:
        f.write(new_html)
    LOGGER.info(f'Saved new HTML to {out_fp}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='議案ファイル（.json）に対し、自動処理された箇所をHTMLで可視化する')
    parser.add_argument('-g', '--gian', help='議案ファイル(.json)', required=True)
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', required=True)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    LOGGER.info(f'Start viz_gian with {args}')

    main(args.gian, args.input, args.output)
