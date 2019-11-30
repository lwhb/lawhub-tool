#!/usr/bin/env python3

"""
法令番号(e.g. 昭和三十五年法律第百四十五号)を受け取り、e-gov法令APIから取得したXMLを保存する

e-gov法令API仕様: https://www.e-gov.go.jp/elaws/interface_api/index.html
"""

import logging
import sys
import xml.etree.ElementTree as ET

import requests

LOGGER = logging.getLogger('get_law')


def fetch(law_num):
    url = f'https://elaws.e-gov.go.jp/api/1/lawdata/{law_num}'
    request = requests.get(url)
    return ET.fromstring(request.text)


def main(law_num, out_fp):
    LOGGER.info(f'Trying to fetch {law_num}')
    root = fetch(law_num)
    try:
        main_provision = root.find('ApplData').find('LawFullText').find('Law').find('LawBody').find('MainProvision')
    except AttributeError as e:
        LOGGER.error(f'failed to find MainProvision: {e}')
        sys.exit(1)
    tree = ET.ElementTree(main_provision)
    tree.write(out_fp, encoding='UTF-8')
    LOGGER.info(f'Saved {out_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, datefmt="%m/%d/%Y %I:%M:%S",
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main(sys.argv[1], sys.argv[2])
