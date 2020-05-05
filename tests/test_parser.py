from unittest import TestCase

from lawhub.action import RenameAction, AddLawAction
from lawhub.law import Article
from lawhub.parser import GianParser, ActionParseResultEntry, LawParseResultEntry, ParseResultEntry, RevisionParseResultEntry


class TestParseResultEntry(TestCase):
    def test_validate_add_law_action_pair_fail(self):
        action_entry = ActionParseResultEntry.from_line('第一条の次に次の二条を加える。', 0)
        law_entry = LawParseResultEntry.from_line('第一条　これは第一項です。', 1)
        with self.assertRaises(ValueError):
            ParseResultEntry._validate_add_law_action_pair(action_entry, law_entry)


class TestGianParser(TestCase):
    def test_parse(self):
        fp = './resource/law.txt'
        with open(fp, 'r') as f:
            lines = [line.strip() for line in f]

        parser = GianParser()
        parse_result = parser.parse(lines)

        self.assertEqual(4, len(parse_result))
        for idx, entry in enumerate(parse_result):
            if idx == 0:
                self.assertTrue(isinstance(entry, RevisionParseResultEntry))
                self.assertEqual(0, entry.idx_start)
                self.assertEqual(2, entry.idx_end)
                self.assertEqual(2, len(entry.lines))
                self.assertEqual('（猫法の一部改正）', entry.lines[0])
                self.assertEqual('第一条　猫法の一部を次のように改正する。', entry.lines[1])
            if idx == 1:
                self.assertTrue(isinstance(entry, ActionParseResultEntry))
                self.assertEqual(2, entry.idx_start)
                self.assertEqual(3, entry.idx_end)
                self.assertEqual(1, len(entry.lines))
                self.assertEqual('この行は変換されない。', entry.lines[0])
                self.assertEqual(0, len(entry.nodes))
                self.assertEqual(False, entry.success)
            elif idx == 2:
                self.assertTrue(isinstance(entry, ActionParseResultEntry))
                self.assertEqual(3, entry.idx_start)
                self.assertEqual(7, entry.idx_end)
                self.assertEqual(4, len(entry.lines))
                self.assertEqual('第一条を第二条とし、目次の次に次の一条を加える。', entry.lines[0])
                self.assertEqual('（テスト）', entry.lines[1])
                self.assertEqual('第一条　これは第一項です。', entry.lines[2])
                self.assertEqual('2　これは第二項です。', entry.lines[3])
                self.assertEqual(2, len(entry.nodes))
                self.assertTrue(isinstance(entry.nodes[0], RenameAction))
                self.assertTrue(isinstance(entry.nodes[1], AddLawAction))
                self.assertEqual(1, len(entry.nodes[1].law))
                self.assertTrue(isinstance(entry.nodes[1].law[0], Article))
                self.assertEqual(True, entry.success)
            elif idx == 3:
                self.assertTrue(isinstance(entry, ActionParseResultEntry))
                self.assertEqual(7, entry.idx_start)
                self.assertEqual(8, entry.idx_end)
                self.assertEqual(1, len(entry.lines))
                self.assertEqual('第二条を第三条とする。', entry.lines[0])
                self.assertEqual(1, len(entry.nodes))
                self.assertTrue(isinstance(entry.nodes[0], RenameAction))
                self.assertEqual(True, entry.success)
