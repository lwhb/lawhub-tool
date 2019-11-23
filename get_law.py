#!/usr/bin/env python3

import sys
import xml.etree.ElementTree as ET

import requests

from lawhub import law


def fetch(law_num):
    url = f'https://elaws.e-gov.go.jp/api/1/lawdata/{law_num}'
    return requests.get(url)


def main(law_num):
    tree = ET.fromstring(fetch(law_num).text)
    main_node = tree.find('ApplData').find('LawFullText').find('Law').find('LawBody').find('MainProvision')
    for node in main_node:
        print(law.parse(node))


if __name__ == '__main__':
    law_num = sys.argv[1]
    main(law_num)
