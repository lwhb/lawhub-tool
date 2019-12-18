import xml.etree.ElementTree as ET
from unittest import TestCase

from lawhub.law import extract_law_hierarchy, LawHierarchy, parse, Article


class TestLaw(TestCase):
    def test_parse(self):
        fp = './resource/law.xml'
        for node in ET.parse(fp).getroot():
            parse(node)

    def test_extract_law_hierarchy(self):
        string = '第七十五条の二の二第五項第三号イ（２）'
        self.assertEqual('第七十五条の二の二', extract_law_hierarchy(string, LawHierarchy.ARTICLE))
        self.assertEqual('第五項', extract_law_hierarchy(string, LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', extract_law_hierarchy(string, LawHierarchy.ITEM))
        self.assertEqual('イ', extract_law_hierarchy(string, LawHierarchy.SUBITEM1))
        self.assertEqual('（２）', extract_law_hierarchy(string, LawHierarchy.SUBITEM2))

    def test_chapter(self):
        fp = './resource/chapter.xml'
        chapter = parse(ET.parse(fp).getroot())
        self.assertEqual('第一章　総則', chapter.title)
        self.assertEqual(0, len(chapter.children))
        self.assertEqual('第一章　総則\n', str(chapter))

    def test_article(self):
        fp = './resource/article.xml'
        article = parse(ET.parse(fp).getroot())
        self.assertEqual('（登記簿等の持出禁止）', article.caption)
        self.assertEqual('第七条の二', article.title)
        self.assertEqual('7_2', article.number)
        self.assertEqual(0, len(article.children))
        self.assertEqual('（登記簿等の持出禁止）\n第七条の二\n', str(article))

    def test_article_order(self):
        self.assertTrue(Article(number='2') < Article(number='10'))
        self.assertTrue(Article(number='2_1') < Article(number='2_2'))
        self.assertTrue(Article(number='2_1') < Article(number='2_10'))
        self.assertTrue(Article(number='2') < Article(number='2_1'))

    def test_item(self):
        fp = './resource/item.xml'
        item = parse(ET.parse(fp).getroot())
        self.assertEqual('第一号', item.title)
        self.assertEqual('ほどほどに頑張ること。', item.sentence)
        self.assertEqual(0, len(item.children))
        self.assertEqual('    一 ほどほどに頑張ること。', str(item))
