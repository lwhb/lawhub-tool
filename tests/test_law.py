import xml.etree.ElementTree as ET
from unittest import TestCase

from lawhub.law import extract_law_hierarchy, LawHierarchy, parse_xml, Article, Chapter, sort_law_tree, Section, INDENT, SPACE, Paragraph


class TestLaw(TestCase):
    def test_parse_xml(self):
        fp = './resource/law.xml'
        for node in ET.parse(fp).getroot():
            parse_xml(node)

    def test_sort_law_tree(self):
        articles = [Article(number='2'), Article(number='3'), Article(number='1')]
        sections = [Section(title='第一節', children=articles)]
        chapter = Chapter(title='第一章', children=sections)

        sort_law_tree(chapter)
        articles = chapter.children[0].children
        self.assertEqual('1', articles[0].number)
        self.assertEqual('2', articles[1].number)
        self.assertEqual('3', articles[2].number)

    def test_extract_law_hierarchy(self):
        string = '第七十五条の二の二第五項第三号イ（２）'
        self.assertEqual('第七十五条の二の二', extract_law_hierarchy(string, LawHierarchy.ARTICLE))
        self.assertEqual('第五項', extract_law_hierarchy(string, LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', extract_law_hierarchy(string, LawHierarchy.ITEM))
        self.assertEqual('イ', extract_law_hierarchy(string, LawHierarchy.SUBITEM1))
        self.assertEqual('（２）', extract_law_hierarchy(string, LawHierarchy.SUBITEM2))

    def test_chapter(self):
        fp = './resource/chapter.xml'
        chapter = parse_xml(ET.parse(fp).getroot())
        self.assertTrue(isinstance(chapter, Chapter))
        self.assertEqual('第一章　総則', chapter.title)
        self.assertEqual(0, len(chapter.children))
        self.assertEqual('第一章　総則\n', str(chapter))

    def test_article(self):
        fp = './resource/article.xml'
        article = parse_xml(ET.parse(fp).getroot())
        self.assertTrue(isinstance(article, Article))
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

    def test_paragraph(self):
        fp = './resource/paragraph.xml'
        paragraph = parse_xml(ET.parse(fp).getroot())
        self.assertTrue(isinstance(paragraph, Paragraph))
        self.assertEqual(1, paragraph.number)
        self.assertEqual('第一項', paragraph.title)
        self.assertEqual('本文ただし書', paragraph.sentence)
        self.assertEqual(0, len(paragraph.children))

    def test_item(self):
        fp = './resource/item.xml'
        item = parse_xml(ET.parse(fp).getroot())
        self.assertEqual('第一号', item.title)
        self.assertEqual('ほどほどに頑張ること。', item.sentence)
        self.assertEqual(0, len(item.children))
        self.assertEqual(INDENT + '一' + SPACE + 'ほどほどに頑張ること。', str(item))
