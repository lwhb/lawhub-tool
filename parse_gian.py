#!/usr/bin/env python3

import argparse
import json
import logging
from pathlib import Path

from lawhub.parser import GianParser
from lawhub.util import StatsFactory

LOGGER = logging.getLogger('parse_gian')


def split_to_chunks(parse_result):
    """
    議案を1改正文=1チャンクになるように分割する
    """

    chunks = []
    prev_idx = 0
    for idx, entry in enumerate(parse_result):
        if '次のように改正する' in ''.join(entry.lines):
            if idx - prev_idx:
                chunks.append(parse_result[prev_idx:idx])
            prev_idx = idx
    chunks.append(parse_result[prev_idx:])
    return chunks


def get_stats(parse_result):
    process_count = 0
    success_count = 0
    for entry in parse_result:
        count = entry.idx_end - entry.idx_start
        process_count += count
        if entry.success:
            success_count += count
    return process_count, success_count


def main(in_fp, stat_fp):
    with open(in_fp, 'r') as f:
        data = json.load(f)
    if 'main' not in data:
        msg = f'"main" does not exists in {in_fp}'
        raise ValueError(msg)
    lines = data['main'].split('\n')

    parser = GianParser()
    parse_result = parser.parse(lines)

    chunks = split_to_chunks(parse_result)
    LOGGER.info(f'Split to {len(chunks)} chunks')

    for chunk_id, chunk in enumerate(chunks):
        out_fp = in_fp.parent / f'{chunk_id}.jsonl'
        with open(out_fp, 'w') as f:
            for entry in chunk:
                f.write(str(entry) + '\n')
        LOGGER.info(f'Saved {out_fp}')

    if stat_fp:
        stats_factory = StatsFactory(['file', 'process', 'success'])
        process_count, success_count = get_stats(parse_result)
        stats_factory.add({'file': in_fp, 'process': process_count, 'success': success_count})
        stats_factory.commit(stat_fp)
        LOGGER.info(f'Appended stats to {stat_fp}')


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='議案ファイル（.json)を受け取り、パースした結果を法案ごとに分けてJSON Lines形式（1.jsonl, 2.jsonl, ...）で保存する')
    argparser.add_argument('-g', '--gian', help='議案ファイル(.json)', required=True)
    argparser.add_argument('-s', '--stat')
    argparser.add_argument('-v', '--verbose', action='store_true')
    args = argparser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    main(Path(args.gian), args.stat)
