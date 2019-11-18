#!/usr/bin/env python3

import sys
import xml.etree.ElementTree as ET

from lawhub import egov


def main(law_num):
    tree = ET.fromstring(egov.fetch(law_num).text)
    main_node = tree.find('ApplData').find('LawFullText').find('Law').find('LawBody').find('MainProvision')
    for node in main_node:
        print(egov.parse(node))


if __name__ == '__main__':
    law_num = sys.argv[1]
    main(law_num)
