from unittest import TestCase

from lawhub.action import parse_action_text, AddLawAction, AddWordAction, DeleteAction, ReplaceAction, RenameAction
from lawhub.query import Query
from lawhub.serializable import is_serializable


class TestAction(TestCase):
    def test_add_law_action(self):
        text = '第二条に次の二項を加え'
        action = parse_action_text(text)

        self.assertTrue(isinstance(action, AddLawAction))
        self.assertEqual(Query.from_text('第二条'), action.at)
        self.assertEqual('二項', action.what)
        self.assertTrue(is_serializable(action))

    def test_add_word_action(self):
        text = '第二条中「前項」の下に「について」を加え'
        action = parse_action_text(text)

        self.assertTrue(isinstance(action, AddWordAction))
        self.assertEqual(Query.from_text('第二条'), action.at)
        self.assertEqual('前項', action.word)
        self.assertEqual('について', action.what)
        self.assertTrue(is_serializable(action))

    def test_add_word_action_short(self):
        text = '「前項」の下に「について」を'
        action = parse_action_text(text)

        self.assertTrue(isinstance(action, AddWordAction))
        self.assertEqual(Query.from_text(''), action.at)
        self.assertEqual('前項', action.word)
        self.assertEqual('について', action.what)
        self.assertTrue(is_serializable(action))

    def test_delete_action(self):
        text = '第十四条中「その他」及び「前項」を削り'
        action = parse_action_text(text)

        self.assertTrue(isinstance(action, DeleteAction))
        self.assertEqual(Query.from_text('第十四条'), action.at)
        self.assertEqual(2, len(action.whats))
        self.assertEqual('その他', action.whats[0])
        self.assertEqual('前項', action.whats[1])
        self.assertTrue(is_serializable(action))

    def test_delete_action_short(self):
        text = '「その他」及び「前項」を削り'
        action = parse_action_text(text)

        self.assertTrue(isinstance(action, DeleteAction))
        self.assertEqual(Query.from_text(''), action.at)
        self.assertEqual(2, len(action.whats))
        self.assertEqual('その他', action.whats[0])
        self.assertEqual('前項', action.whats[1])
        self.assertTrue(is_serializable(action))

    def test_replace_action(self):
        text = '第一条中「第百二十五条」を「第百二十五条の二」に改める'
        action = parse_action_text(text)

        self.assertTrue(isinstance(action, ReplaceAction))
        self.assertEqual(Query.from_text('第一条'), action.at)
        self.assertEqual('第百二十五条', action.old)
        self.assertEqual('第百二十五条の二', action.new)
        self.assertTrue(is_serializable(action))

    def test_replace_action_short(self):
        text = '「第百二十五条」を「第百二十五条の二」に'
        action = parse_action_text(text)

        self.assertTrue(isinstance(action, ReplaceAction))
        self.assertEqual(Query.from_text(''), action.at)
        self.assertEqual('第百二十五条', action.old)
        self.assertEqual('第百二十五条の二', action.new)
        self.assertTrue(is_serializable(action))

    def test_rename_action(self):
        text = '一条中第三項を第四項とする'
        action = parse_action_text(text)

        self.assertTrue(isinstance(action, RenameAction))
        self.assertEqual(Query.from_text('一条中第三項'), action.old)
        self.assertEqual(Query.from_text('第四項'), action.new)
        self.assertTrue(is_serializable(action))

    def test_invalid_action_fail(self):
        text = 'ランダムな文'
        with self.assertRaises(ValueError):
            parse_action_text(text)
