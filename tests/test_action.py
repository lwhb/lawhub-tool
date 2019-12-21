from unittest import TestCase

from lawhub.action import Action, ActionType
from lawhub.query import Query


class TestAction(TestCase):
    def test_init_add(self):
        text = '第二条に次の二項を加え'
        action = Action(text)

        self.assertEqual(ActionType.ADD, action.action_type)
        self.assertEqual(Query('第二条'), action.at)
        self.assertEqual('次の二項', action.what)

    def test_init_add_after(self):
        text = '第二条中「前項」の下に「について」を加え'
        action = Action(text)

        self.assertEqual(ActionType.ADD_AFTER, action.action_type)
        self.assertEqual(Query('第二条'), action.at)
        self.assertEqual('前項', action.word)
        self.assertEqual('について', action.what)

    def test_init_add_after_short(self):
        text = '「前項」の下に「について」を'
        action = Action(text)

        self.assertEqual(ActionType.ADD_AFTER, action.action_type)
        self.assertEqual(Query(''), action.at)
        self.assertEqual('前項', action.word)
        self.assertEqual('について', action.what)

    def test_init_delete(self):
        text = '第十四条中「その他」及び「前項」を削り'
        action = Action(text)

        self.assertEqual(ActionType.DELETE, action.action_type)
        self.assertEqual(Query('第十四条'), action.at)
        self.assertEqual(2, len(action.whats))
        self.assertEqual('その他', action.whats[0])
        self.assertEqual('前項', action.whats[1])

    def test_init_replace(self):
        text = '第一条中「第百二十五条」を「第百二十五条の二」に改める'
        action = Action(text)

        self.assertEqual(ActionType.REPLACE, action.action_type)
        self.assertEqual(Query('第一条'), action.at)
        self.assertEqual('第百二十五条', action.old)
        self.assertEqual('第百二十五条の二', action.new)

    def test_init_replace_short(self):
        text = '「第百二十五条」を「第百二十五条の二」に'
        action = Action(text)

        self.assertEqual(ActionType.REPLACE, action.action_type)
        self.assertEqual(Query(''), action.at)
        self.assertEqual('第百二十五条', action.old)
        self.assertEqual('第百二十五条の二', action.new)

    def test_init_rename(self):
        text = '一条中第三項を第四項とする'
        action = Action(text)

        self.assertEqual(ActionType.RENAME, action.action_type)
        self.assertEqual(Query('一条中第三項'), action.old)
        self.assertEqual(Query('第四項'), action.new)

    def test_init_fail(self):
        text = 'ランダムな文'
        with self.assertRaises(ValueError):
            Action(text)
