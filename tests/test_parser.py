from unittest import TestCase, skip

from lawhub.action import RenameAction, AddLawAction
from lawhub.law import Article, Paragraph
from lawhub.parser import GianParser

@skip
class TestGianParser(TestCase):
    def test_parse(self):
        fp = './resource/law.txt'
        with open(fp, 'r') as f:
            lines = [line.strip() for line in f]

        parser = GianParser(lines)
        lines_and_nodes = parser.parse()
        self.assertEqual(4, len(lines_and_nodes))

        line = lines_and_nodes[0]
        self.assertTrue(isinstance(line, str))
        self.assertEqual('この行は変換されない。', lines_and_nodes[0])

        action1 = lines_and_nodes[1]
        self.assertTrue(isinstance(action1, RenameAction))
        self.assertEqual('第一条を第二条とし', action1.text)
        self.assertEqual(1, action1.meta['line'])

        action2 = lines_and_nodes[2]
        self.assertTrue(isinstance(action2, AddLawAction))
        self.assertEqual('目次の次に次の一条を加える', action2.text)
        self.assertEqual(1, action2.meta['line'])

        law = action2.law
        self.assertEqual(1, len(law))
        article = law[0]
        self.assertTrue(isinstance(article, Article))
        self.assertEqual('（テスト）', article.caption)
        self.assertEqual('第一条', article.title)
        self.assertEqual(2, len(article.children))
        paragraph1 = article.children[0]
        paragraph2 = article.children[1]
        self.assertTrue(isinstance(paragraph1, Paragraph))
        self.assertEqual(1, paragraph1.number)
        self.assertEqual('これは第一項です。', paragraph1.sentence)
        self.assertTrue(isinstance(paragraph2, Paragraph))
        self.assertEqual(2, paragraph2.number)
        self.assertEqual('これは第二項です。', paragraph2.sentence)

        action3 = lines_and_nodes[3]
        self.assertTrue(isinstance(action3, RenameAction))
        self.assertEqual('第二条を第三条とする', action3.text)
        self.assertEqual(5, action3.meta['line'])

        self.assertEqual(5, parser.success_count)
