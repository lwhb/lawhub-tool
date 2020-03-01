#!/usr/bin/env python3
import argparse
import logging

from lawhub.parser import GianParser

LOGGER = logging.getLogger('format_law')


def main(in_fp, out_fp):
    with open(in_fp, 'r') as f:
        lines = [line.strip() for line in f]
    LOGGER.info(f'Loaded text from {in_fp}')

    gian_parser = GianParser()
    lines_and_nodes = gian_parser.parse(lines)

    with open(out_fp, 'w') as f:
        for obj in lines_and_nodes:
            if isinstance(obj, str):
                LOGGER.warning(f'failed to convert {obj} to law node')
                f.write('!!' + obj + '\n')
            else:
                f.write(str(obj) + '\n')
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
