#!/usr/bin/env python3

"""
JSONLinesを受け取り、改正対象の法令をXMLとして保存する
"""

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
    with open(jsonl_fp, 'r') as f:
        match = re.search(PATTERN_LAW_NUMBER, f.read())
        if match:
            return match.group()
    return None


def main(jsonl_fp, xml_fp):
    LOGGER.info(f'Start getting target of {jsonl_fp}')

    if xml_fp.exists():
        LOGGER.info(f'{xml_fp} already exists')
        sys.exit(0)
    LOGGER.info(f'{xml_fp} does not exist yet')

    law_num = extract_law_num(jsonl_fp)
    if law_num is None:
        LOGGER.error(f'Failed to extract target law number from {jsonl_fp}')
        sys.exit(1)
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
    logging.basicConfig(level=logging.INFO, datefmt="%m/%d/%Y %I:%M:%S",
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
