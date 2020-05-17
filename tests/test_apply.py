from unittest import TestCase

from lawhub.action import parse_action_text
from lawhub.apply import apply_replace, TextNotFoundError, MultipleTextFoundError, apply_add_word, apply_delete
from lawhub.law import Paragraph, LawNodeFinder


class TestApply(TestCase):
    def test_apply_replace(self):
        node = Paragraph(title='第一項', sentence='私はネコです')
        node_finder = LawNodeFinder([node])
        action = parse_action_text('第一項中「ネコ」を「イヌ」に改める')

        apply_replace(action, node_finder)
        self.assertEqual('私はイヌです', node.sentence)

    def test_apply_replace_fail(self):
        node = Paragraph(title='第一項', sentence='私はネコです')
        node_finder = LawNodeFinder([node])
        action = parse_action_text('第一項中「サル」を「イヌ」に改める')

        with self.assertRaises(TextNotFoundError):
            apply_replace(action, node_finder)

    def test_apply_replace_multiple_fail(self):
        node = Paragraph(title='第一項', sentence='私はネコネコです')
        node_finder = LawNodeFinder([node])
        action = parse_action_text('第一項中「ネコ」を「イヌ」に改める')

        with self.assertRaises(MultipleTextFoundError):
            apply_replace(action, node_finder)

    def test_apply_add_word(self):
        node = Paragraph(title='第一項', sentence='私はネコです')
        node_finder = LawNodeFinder([node])
        action = parse_action_text('第一項中「ネコ」の下に「ザメ」を加える')

        apply_add_word(action, node_finder)
        self.assertEqual('私はネコザメです', node.sentence)

    def test_apply_add_word_fail(self):
        node = Paragraph(title='第一項', sentence='私はネコです')
        node_finder = LawNodeFinder([node])
        action = parse_action_text('第一項中「サル」の下に「ザメ」を加える')

        with self.assertRaises(TextNotFoundError):
            apply_add_word(action, node_finder)

    def test_apply_delete(self):
        node = Paragraph(title='第一項', sentence='私はネコです')
        node_finder = LawNodeFinder([node])
        action = parse_action_text('第一項中「私は」及び「です」を削る')

        apply_delete(action, node_finder)
        self.assertEqual('ネコ', node.sentence)

    def test_apply_delete_fail(self):
        node = Paragraph(title='第一項', sentence='私はネコです')
        node_finder = LawNodeFinder([node])
        action = parse_action_text('第一項中「私は」及び「でした」を削る')

        with self.assertRaises(TextNotFoundError):
            apply_delete(action, node_finder)
        self.assertEqual('私はネコです', node.sentence)  # not changed
