#!/usr/bin/env python3

import argparse
import logging
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

from lawhub.constants import PATTERN_LAW_NUMBER

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


def extract_law_num(jsonl_fp):
    """
    JSONLineを受け取り、法令番号が存在すれば返す
    :param jsonl_fp:
    :return: 法令番号又は改正行が存在しなければNone
    :raises ValueError: 改正行はあるが法令番号が取得できなかった場合
    """
    target_line = None
    with open(jsonl_fp, 'r') as f:
        for line in f:
            if 'の一部を次のように改正する' in line:
                target_line = line.strip()
    if target_line is None:
        return None
    pattern = r'（({})）の一部を次のように改正する'.format(PATTERN_LAW_NUMBER)
    match = re.search(pattern, target_line)
    if match is None:
        msg = f'failed to extract law number from {target_line}'
        raise ValueError(msg)
    return match.group(1)


def main(jsonl_fp, xml_fp):
    if xml_fp.exists():
        LOGGER.info(f'Skips as law file already exists ({xml_fp})')
        sys.exit(0)

    LOGGER.info(f'Start getting target of {jsonl_fp}')
    try:
        law_num = extract_law_num(jsonl_fp)
    except ValueError as e:
        LOGGER.error(e)
        sys.exit(1)
    if law_num is None:
        LOGGER.info(f'{jsonl_fp} does not contain KAISEI line')
        sys.exit(0)
    LOGGER.info(f'Extracted target law: {law_num}')

    try:
        root = fetch_law(law_num)
        main_provision = root.find('ApplData').find('LawFullText').find('Law').find('LawBody').find('MainProvision')
        tree = ET.ElementTree(main_provision)
        time.sleep(1)
    except AttributeError as e:
        LOGGER.error(f'Failed to find MainProvision: {e}')
        sys.exit(1)
    LOGGER.info(f'Fetched XML from e-govAPI')

    tree.write(xml_fp, encoding='UTF-8')
    LOGGER.info(f'Saved {xml_fp}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JSONLinesを受け取り、改正対象の法令をXMLとして保存する')
    parser.add_argument('-g', '--gian', help='議案ファイル(.jsonl)')
    parser.add_argument('-l', '--law', help='法律ファイル(.xml)', required=True)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    main(Path(args.gian), Path(args.law))
