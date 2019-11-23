#!/usr/bin/env python3

import xml.etree.ElementTree as ET

import requests


def fetch(law_num):
    url = f'https://elaws.e-gov.go.jp/api/1/lawdata/{law_num}'
    request = requests.get(url)
    return ET.fromstring(request.text)


def main(law_num, out_fp):
    root = fetch(law_num)
    main_provision = root.find('ApplData').find('LawFullText').find('Law').find('LawBody').find('MainProvision')
    tree = ET.ElementTree(main_provision)
    tree.write(out_fp, encoding='UTF-8')


if __name__ == '__main__':
    law_num = '平成二十一年法律第六十六号'
    out_fp = './law.xml'
    main(law_num, out_fp)
