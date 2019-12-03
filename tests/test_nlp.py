from unittest import TestCase

from lawhub.nlp import normalize_last_verb, split_with_escape


class TestNlp(TestCase):
    def test_normalize_last_verb(self):
        sentence = '第二項を第三項とし'
        self.assertEqual('第二項を第三項とする', normalize_last_verb(sentence))

    def test_normalize_last_verb_non_verb(self):
        sentence = 'この場合において'
        self.assertEqual(sentence, normalize_last_verb(sentence))

    def test_split_with_escape(self):
        sentence = 'この関数は「かっこ（「」）で、囲まれていると」切らない、らしい。'
        self.assertEqual(['この関数は「かっこ（「」）で、囲まれていると」切らない', 'らしい'], split_with_escape(sentence))
