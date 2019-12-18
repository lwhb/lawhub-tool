import xml.etree.ElementTree as ET
from unittest import TestCase

from lawhub.law import extract_law_hierarchy, LawHierarchy, parse


class TestLaw(TestCase):
    def test_extract_law_hierarchy(self):
        string = '第七十五条の二の二第五項第三号イ（２）'

        self.assertEqual('第七十五条の二の二', extract_law_hierarchy(string, LawHierarchy.ARTICLE))
        self.assertEqual('第五項', extract_law_hierarchy(string, LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', extract_law_hierarchy(string, LawHierarchy.ITEM))
        self.assertEqual('イ', extract_law_hierarchy(string, LawHierarchy.SUBITEM1))
        self.assertEqual('（２）', extract_law_hierarchy(string, LawHierarchy.SUBITEM2))

    def test_article(self):
        node = ET.parse('./resource/Article.xml').getroot()
        article = parse(node)
        self.assertEqual('（登記簿等の持出禁止）', article.caption)
        self.assertEqual('第七条の二', article.title)
        self.assertEqual('7_2', article.number)
