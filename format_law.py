#!/usr/bin/env python3
import argparse
import logging
import sys

from lawhub.law import build_law_tree

LOGGER = logging.getLogger('format_law')


def main(in_fp, out_fp):
    with open(in_fp, 'r') as f:
        text = f.read()
    LOGGER.info(f'Loaded text from {in_fp}')

    try:
        tree = build_law_tree(text)
    except Exception as e:
        LOGGER.error(f'Failed to build law tree', e)
        sys.exit(1)
    LOGGER.info('Successfully build law tree')

    with open(out_fp, 'w') as f:
        for node in tree:
            f.write(str(node) + '\n')
    LOGGER.info(f'Saved formatted text to {out_fp}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='生TEXTの法律文を受け取り整形して出力する')
    parser.add_argument('-i', '--input', default='./data/format_law.in')
    parser.add_argument('-o', '--output', default='./data/format_law.out')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    main(args.input, args.output)
