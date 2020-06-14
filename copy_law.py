#!/usr/bin/env python3

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

import pandas as pd
from git import Repo

from lawhub.constants import LAWHUB_ROOT, LOG_DATE_FORMAT, LOG_FORMAT
from lawhub.law import extract_target_law_meta

LOGGER = logging.getLogger('copy_law')


class LawFinder:
    LAWHUB_XML = LAWHUB_ROOT / 'lawhub-xml'

    def __init__(self):
        self.repo = Repo(self.LAWHUB_XML)
        self.df = pd.read_csv(self.LAWHUB_XML / 'index.tsv', sep='\t')

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
        return

    try:
        with open(jsonl_fp, 'r') as f:
            line = f.readline().strip()
        LOGGER.debug(f'extract target law from {line}')
        meta = extract_target_law_meta(line)
    except ValueError as e:
        LOGGER.info(f'skip copying as no target law found, likely this is not 改正法案: {e}')
        return
    LOGGER.info(f'extracted target law: {meta}')

    law_finder = LawFinder()
    try:
        xml_fp = law_finder.find_by_number(meta['LawNum']) if 'LawNum' in meta else law_finder.find_by_title(meta['LawTitle'])
    except ValueError as e:
        LOGGER.error(f'failed to find target law in lawhub-xml: {e}')
        sys.exit(1)
    LOGGER.info(f'found target law in lawhub-xml: {xml_fp}')

    shutil.copy(str(xml_fp), str(out_fp))
    LOGGER.info(f'Copied {xml_fp} to {out_fp}')

    meta_fp = str(out_fp) + '.meta'
    meta['fp'] = str(xml_fp)
    meta['tag'] = str(law_finder.repo.tags[-1])
    with open(meta_fp, 'w') as f:
        json.dump(meta, f, ensure_ascii=False)
    LOGGER.info(f'Saved meta data in {meta_fp}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JSON Lines形式にパースされた議案ファイルを受け取り、改正対象のXMLを法令をlawhub-xmlからコピーする')
    parser.add_argument('-g', '--gian', help='議案ファイル(.jsonl)', required=True)
    parser.add_argument('-o', '--out', help='コピー先(.xml)', required=True)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, datefmt=LOG_DATE_FORMAT, format=LOG_FORMAT)

    main(Path(args.gian), Path(args.out))
