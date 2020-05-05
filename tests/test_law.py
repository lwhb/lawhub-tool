import xml.etree.ElementTree as ET
from unittest import TestCase

from lawhub.law import LawHierarchy, parse_xml, Article, Chapter, sort_law_tree, Section, INDENT, SPACE, Paragraph, LawTreeBuilder, Item, line_to_law_node
from lawhub.serializable import is_serializable


class TestLaw(TestCase):
    def test_parse_xml(self):
        fp = './resource/law.xml'
        for node in ET.parse(fp).getroot():
            tree = parse_xml(node)
            self.assertTrue(is_serializable(tree))

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
        self.assertEqual('第七十五条の二の二', LawHierarchy.ARTICLE.extract(string))
        self.assertEqual('第五項', LawHierarchy.PARAGRAPH.extract(string))
        self.assertEqual('第三号', LawHierarchy.ITEM.extract(string))
        self.assertEqual('イ', LawHierarchy.SUBITEM1.extract(string))
        self.assertEqual('（２）', LawHierarchy.SUBITEM2.extract(string))

        string = '同条第一項'
        self.assertEqual('同条', LawHierarchy.ARTICLE.extract(string))
        self.assertEqual('', LawHierarchy.ARTICLE.extract(string, allow_placeholder=False))
        self.assertEqual('', LawHierarchy.ARTICLE.extract(string, allow_partial_match=False))
        self.assertEqual('第一項', LawHierarchy.PARAGRAPH.extract(string))
        self.assertEqual('第一項', LawHierarchy.PARAGRAPH.extract(string, allow_placeholder=False))
        self.assertEqual('', LawHierarchy.PARAGRAPH.extract(string, allow_partial_match=False))

    def test_get_child_hierarchy_list(self):
        self.assertEqual(
            [LawHierarchy.ITEM, LawHierarchy.SUBITEM1, LawHierarchy.SUBITEM2, LawHierarchy.SUBITEM3],
            LawHierarchy.PARAGRAPH.get_children()
        )

    def test_chapter(self):
        fp = './resource/chapter.xml'
        chapter = parse_xml(ET.parse(fp).getroot())
        self.assertTrue(isinstance(chapter, Chapter))
        self.assertEqual('第一章　総則', chapter.title)
        self.assertEqual(0, len(chapter.children))
        self.assertEqual('第一章　総則\n', str(chapter))
        self.assertTrue(is_serializable(chapter))

    def test_article(self):
        fp = './resource/article.xml'
        article = parse_xml(ET.parse(fp).getroot())
        self.assertTrue(isinstance(article, Article))
        self.assertEqual('（登記簿等の持出禁止）', article.caption)
        self.assertEqual('第七条の二', article.title)
        self.assertEqual('7_2', article.number)
        self.assertEqual(0, len(article.children))
        self.assertEqual('（登記簿等の持出禁止）\n第七条の二\n', str(article))
        self.assertTrue(is_serializable(article))

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
        self.assertTrue(is_serializable(paragraph))

    def test_item(self):
        fp = './resource/item.xml'
        item = parse_xml(ET.parse(fp).getroot())
        self.assertEqual('第一号', item.title)
        self.assertEqual('ほどほどに頑張ること。', item.sentence)
        self.assertEqual(0, len(item.children))
        self.assertEqual(INDENT + '一' + SPACE + 'ほどほどに頑張ること。', str(item))
        self.assertTrue(is_serializable(item))

    def test_law_tree_biulder(self):
        input_nodes = [
            Chapter(title='第一章'),
            Article(caption='テスト'),
            Article(title='第一条', children=[Paragraph(title='第一条第一項')]),
            Item(title='一'),
            Item(title='二'),
            Paragraph(title='第一条第二項'),
            Article(title='第二条'),
            Paragraph(title='第二条第一項')
        ]

        builder = LawTreeBuilder()
        for node in input_nodes[::-1]:
            builder.add(node)
        output_nodes = builder.build()

        self.assertEqual(1, len(output_nodes))
        chapter = output_nodes[0]
        self.assertEqual('第一章', chapter.title)
        self.assertEqual(2, len(chapter.children))
        article1 = chapter.children[0]
        self.assertEqual('第一条', article1.title)
        self.assertEqual('テスト', article1.caption)
        self.assertEqual(2, len(article1.children))
        paragraph1 = article1.children[0]
        self.assertEqual('第一条第一項', paragraph1.title)
        self.assertEqual(2, len(paragraph1.children))
        item1 = paragraph1.children[0]
        self.assertEqual('第一号', item1.title)
        self.assertEqual(0, len(item1.children))
        item2 = paragraph1.children[1]
        self.assertEqual('第二号', item2.title)
        self.assertEqual(0, len(item2.children))
        paragraph2 = article1.children[1]
        self.assertEqual('第一条第二項', paragraph2.title)
        self.assertEqual(0, len(paragraph2.children))
        article2 = chapter.children[1]
        self.assertEqual('第二条', article2.title)
        self.assertEqual('', article2.caption)
        self.assertEqual(1, len(article2.children))
        paragraph3 = article2.children[0]
        self.assertEqual('第二条第一項', paragraph3.title)

    def test_law_tree_builder_empty(self):
        builder = LawTreeBuilder()
        self.assertEqual(list(), builder.build())

    def test_law_tree_builder_add_fail(self):
        article = Article(title='第一条')
        item = Item(title='第一号')
        paragraph = Paragraph(title='第一項')

        law_tree_builder = LawTreeBuilder()
        law_tree_builder.add(paragraph)
        law_tree_builder.add(item)
        with self.assertRaises(ValueError):
            law_tree_builder.add(article)  # failed to add as multiple children exists at different hierarchy

    def test_line_to_law_node(self):
        self.assertEqual(
            Article(title='第一条', children=Paragraph(title='第一項', number=1, sentence='これは第一項です。')),
            line_to_law_node('第一条　これは第一項です。')
        )
        self.assertEqual(
            Paragraph(number=2, sentence='これは第二項です。'),
            line_to_law_node('２　これは第二項です。')
        )
        self.assertEqual(
            Article(caption='（テスト）'),
            line_to_law_node('（テスト）')
        )
        self.assertEqual(
            Item(title='一の二', sentence='これは第一の二号です。'),
            line_to_law_node('一の二　これは第一の二号です。')
        )
