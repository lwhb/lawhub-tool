from unittest import TestCase

from lawhub.action import Action
from lawhub.apply import apply_replace, TextNotFoundError, apply_add_after
from lawhub.law import Paragraph
from lawhub.query import Query


class TestApply(TestCase):
    def test_apply_replace(self):
        node = Paragraph(title='第一項', sentence='私はネコです')
        action = Action('第一項中「ネコ」を「イヌ」に改める')
        query2node = {Query('第一項'): node}

        apply_replace(action, query2node)
        self.assertEqual('私はイヌです', node.sentence)

    def test_apply_replace_fail(self):
        node = Paragraph(title='第一項', sentence='私はネコです')
        action = Action('第一項中「サル」を「イヌ」に改める')
        query2node = {Query('第一項'): node}

        with self.assertRaises(TextNotFoundError):
            apply_replace(action, query2node)

    def test_add_after(self):
        node = Paragraph(title='第一項', sentence='私はネコです')
        action = Action('第一項中「ネコ」の下に「ザメ」を加える')
        query2node = {Query('第一項'): node}

        apply_add_after(action, query2node)
        self.assertEqual('私はネコザメです', node.sentence)

    def test_add_after_fail(self):
        node = Paragraph(title='第一項', sentence='私はネコです')
        action = Action('第一項中「サル」の下に「ザメ」を加える')
        query2node = {Query('第一項'): node}

        with self.assertRaises(TextNotFoundError):
            apply_add_after(action, query2node)
