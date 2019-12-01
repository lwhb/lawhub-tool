from unittest import TestCase

from lawhub.action import Action
from lawhub.query import Query


class TestAction(TestCase):
    def test_init_add(self):
        text = '第二条に次の二項を加える'
        action = Action(text)

        self.assertEqual(action.at, Query('第二条'))
        self.assertEqual(action.what, '次の二項')

    def test_init_delete(self):
        text = '第十四条中「その他」を削る'
        action = Action(text)

        self.assertEqual(action.at, Query('第十四条'))
        self.assertEqual(action.what, 'その他')

    def test_init_replace(self):
        text = '第一条中「第百二十五条」を「第百二十五条の二」に改める'
        action = Action(text)

        self.assertEqual(action.at, Query('第一条'))
        self.assertEqual(action.old, '第百二十五条')
        self.assertEqual(action.new, '第百二十五条の二')

    def test_init_rename(self):
        text = '一条中第三項を第四項とする'
        action = Action(text)

        self.assertEqual(action.old, Query('一条中第三項'))
        self.assertEqual(action.new, Query('第四項'))

    def test_init_fail(self):
        text = 'ランダムな文'
        with self.assertRaises(ValueError):
            Action(text)
