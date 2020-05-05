#!/usr/bin/env python3
import argparse
import logging

from lawhub.parser import GianParser

LOGGER = logging.getLogger('format_law')


def main(in_fp, out_fp):
    with open(in_fp, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    LOGGER.info(f'Loaded text from {in_fp}')

    parser = GianParser()
    parse_result = parser.parse(lines)

    with open(out_fp, 'w') as f:
        for entry in parse_result:
            for node in entry.nodes:
                f.write(f'{node}\n')
    LOGGER.info(f'Saved formatted text to {out_fp}')


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='生TEXTの法律文を受け取り整形して出力する')
    argparser.add_argument('-i', '--input', default='./data/format_law.in')
    argparser.add_argument('-o', '--output', default='./data/format_law.out')
    argparser.add_argument('-v', '--verbose', action='store_true')
    args = argparser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    main(args.input, args.output)
