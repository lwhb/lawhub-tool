#!/usr/bin/env python3

import argparse
import logging
import shutil
import sys
from pathlib import Path

import pandas as pd

from lawhub.constants import LAWHUB_ROOT
from lawhub.law import extract_target_law_meta

LOGGER = logging.getLogger('copy_law')


class LawFinder:
    LAWHUB_XML = LAWHUB_ROOT / 'lawhub-xml'

    def __init__(self):
        fp = self.LAWHUB_XML / 'index.tsv'
        self.df = pd.read_csv(fp, sep='\t')

    def find_by_number(self, law_num):
        query = f'LawNum == "{law_num}"'
        return self.find_by_query(query)

    def find_by_title(self, law_title):
        query = f'LawTitle == "{law_title}"'
        return self.find_by_query(query)

    def find_by_query(self, query):
        result = self.df.query(query)
        if len(result) == 0:
            raise ValueError(f'failed to find xml that match {query}')
        elif len(result) == 1:
            return self.LAWHUB_XML / result['fp'].iloc[0]
        else:
            raise ValueError(f'found multiple xml that match {query}: {result}')


def main(jsonl_fp, out_fp):
    LOGGER.info(f'Start copying target of {jsonl_fp}')

    if out_fp.exists():
        LOGGER.info(f'skip copying as law file already exists: {out_fp}')
        sys.exit(0)

    try:
        with open(jsonl_fp, 'r') as f:
            line = f.readline().strip()
        LOGGER.debug(f'extract target law from {line}')
        meta = extract_target_law_meta(line)
    except ValueError as e:
        LOGGER.info(f'skip copying as no target law found, likely this is not 改正法案: {e}')
        sys.exit(0)
    LOGGER.info(f'extracted target law: {meta}')

    try:
        law_finder = LawFinder()
        xml_fp = law_finder.find_by_number(meta['LawNum']) if 'LawNum' in meta else law_finder.find_by_title(meta['LawTitle'])
    except ValueError as e:
        LOGGER.error(f'failed to find target law in lawhub-xml: {e}')
        sys.exit(1)
    LOGGER.info(f'found target law in lawhub-xml: {xml_fp}')

    shutil.copy(str(xml_fp), str(out_fp))
    LOGGER.info(f'Copied {xml_fp} to {out_fp}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JSONLinesを受け取り、改正対象のXMLを法令をlawhub-xmlからコピーする')
    parser.add_argument('-g', '--gian', help='議案ファイル(.jsonl)', required=True)
    parser.add_argument('-o', '--out', help='コピー先', required=True)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    main(Path(args.gian), Path(args.out))
