#!/usr/bin/env python3

import argparse
import logging
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

from lawhub.constants import LOG_DATE_FORMAT, LOG_FORMAT
from lawhub.law import extract_target_law_meta

LOGGER = logging.getLogger('get_law')


def fetch_law(law_num):
    """
    法令番号(e.g. 昭和三十五年法律第百四十五号)を受け取り、e-gov法令APIから取得したXMLを返す
    e-gov法令API仕様: https://www.e-gov.go.jp/elaws/interface_api/index.html

    :param law_num: 法令番号
    :return: root element of XML tree
    """
    url = f'https://elaws.e-gov.go.jp/api/1/lawdata/{law_num}'
    request = requests.get(url)
    return ET.fromstring(request.text)


def main(jsonl_fp, xml_fp):
    LOGGER.info(f'Start fetching target of {jsonl_fp}')

    if xml_fp.exists():
        LOGGER.info(f'Skip fetching as law file already exists ({xml_fp})')
        sys.exit(0)

    try:
        with open(jsonl_fp, 'r') as f:
            line = f.readline().strip()
        LOGGER.debug(f'extract target law from {line}')
        meta = extract_target_law_meta(line)
    except ValueError as e:
        LOGGER.info(f'skip fetching as no target law found, likely this is not 改正法案: {e}')
        sys.exit(0)
    LOGGER.info(f'extracted target law: {meta}')

    try:
        root = fetch_law(meta['LawNum'])
        law = root.find('ApplData').find('LawFullText').find('Law')
        tree = ET.ElementTree(law)
        time.sleep(1)
    except AttributeError as e:
        LOGGER.error(f'Failed to find Law: {e}')
        sys.exit(1)
    LOGGER.info(f'Fetched XML from e-Gov API')

    tree.write(xml_fp, encoding='UTF-8')
    LOGGER.info(f'Saved {xml_fp}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JSONLinesを受け取り、改正対象の法令をe-Govからfetchする')
    parser.add_argument('-g', '--gian', help='議案ファイル(.jsonl)', required=True)
    parser.add_argument('-o', '--out', help='保存先', required=True)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, datefmt=LOG_DATE_FORMAT, format=LOG_FORMAT)

    main(Path(args.gian), Path(args.law))
