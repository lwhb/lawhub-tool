#!/usr/bin/env python3

import argparse
import json
import logging
from pathlib import Path

from lawhub.parser import GianParser
from lawhub.util import StatsFactory

LOGGER = logging.getLogger('parse_gian')


def split_to_chunks(lines_and_nodes):
    """
    議案を1改正文=1チャンクになるように分割する
    """

    chunks = []
    prev_idx = 0
    for idx, obj in enumerate(lines_and_nodes):
        if '次のように改正する' in str(obj):
            if idx - prev_idx:
                chunks.append(lines_and_nodes[prev_idx:idx])
            prev_idx = idx
    chunks.append(lines_and_nodes[prev_idx:])
    return chunks


def main(in_fp, stat_fp):
    with open(in_fp, 'r') as f:
        data = json.load(f)
    if 'main' not in data:
        msg = f'"main" does not exists in {in_fp}'
        raise ValueError(msg)
    lines = data['main'].split('\n')

    gian_parser = GianParser(lines)
    lines_and_nodes = gian_parser.parse()
    # LOGGER.info(f'Parsed {gian_parser.success_count} / {gian_parser.process_count} lines')

    chunks = split_to_chunks(lines_and_nodes)
    LOGGER.info(f'Split to {len(chunks)} chunks')

    for chunk_id, chunk in enumerate(chunks):
        out_fp = in_fp.parent / f'{chunk_id}.jsonl'
        with open(out_fp, 'w') as f:
            for obj in chunk:
                if isinstance(obj, str):
                    f.write('!!' + obj + '\n')
                else:
                    f.write(obj.serialize() + '\n')
        LOGGER.info(f'Saved {out_fp}')

    if stat_fp:
        stats_factory = StatsFactory(['file', 'process', 'success'])
        # stats_factory.add({'file': in_fp, 'process': gian_parser.process_count, 'success': gian_parser.success_count})
        stats_factory.commit(stat_fp)
        LOGGER.info(f'Appended stats to {stat_fp}')


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
