from unittest import TestCase

from lawhub.nlp import normalize_last_verb, split_with_escape, mask_escape


class TestNlp(TestCase):
    def test_normalize_last_verb(self):
        sentence = '第二項を第三項とし'
        self.assertEqual('第二項を第三項とする', normalize_last_verb(sentence))

    def test_normalize_last_verb_non_verb(self):
        sentence = 'この場合において'
        self.assertEqual(sentence, normalize_last_verb(sentence))

    def test_normalize_last_verb_empty(self):
        sentence = ''
        self.assertEqual(sentence, normalize_last_verb(sentence))

    def test_split_with_escape(self):
        sentence = 'この関数は「かっこ（「」）で、囲まれていると」切らない、らしい。'
        self.assertEqual(['この関数は「かっこ（「」）で、囲まれていると」切らない', 'らしい'], split_with_escape(sentence))

    def test_mask_escape(self):
        sentence = 'この関数は「かっこ（「」）」を「マスク」するらしい'
        masked_sentence, placeholder_map = mask_escape(sentence)
        self.assertEqual('この関数は{A}を{B}するらしい', masked_sentence)
        self.assertEqual('「かっこ（「」）」', placeholder_map['A'])
        self.assertEqual('「マスク」', placeholder_map['B'])
        self.assertEqual(sentence, masked_sentence.format(**placeholder_map))
