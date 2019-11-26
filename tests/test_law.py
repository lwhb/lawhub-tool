from unittest import TestCase

from lawhub.law import extract_law_hierarchy, LawHierarchy


class TestLaw(TestCase):
    def test_extract_law_hierarchy(self):
        string = '第七十五条の二の二第五項第三号イ（２）'

        self.assertEqual('第七十五条の二の二', extract_law_hierarchy(string, LawHierarchy.ARTICLE))
        self.assertEqual('第五項', extract_law_hierarchy(string, LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', extract_law_hierarchy(string, LawHierarchy.ITEM))
        self.assertEqual('イ', extract_law_hierarchy(string, LawHierarchy.SUBITEM1))
        self.assertEqual('（２）', extract_law_hierarchy(string, LawHierarchy.SUBITEM2))
