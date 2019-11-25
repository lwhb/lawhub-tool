#!/usr/bin/env python3

import logging
import sys
import xml.etree.ElementTree as ET

import requests

LOGGER = logging.getLogger(__name__)


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
