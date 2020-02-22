from unittest import TestCase

from lawhub.law import LawHierarchy
from lawhub.query import Query, QueryCompensator


class TestQuery(TestCase):
    def test_init_at_hierarchy(self):
        text = '第一条第二項第三号'
        query = Query.from_text(text)

        self.assertEqual('第一条', query.get(LawHierarchy.ARTICLE))
        self.assertEqual('第二項', query.get(LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', query.get(LawHierarchy.ITEM))

    def test_init_after_hierarchy(self):
        text = '第一条第二項第三号の次'
        query = Query.from_text(text)

        self.assertEqual('第一条', query.get(LawHierarchy.ARTICLE))
        self.assertEqual('第二項', query.get(LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', query.get(LawHierarchy.ITEM))


class TestQueryCompensator(TestCase):
    def test_compensate_success(self):
        qc = QueryCompensator()
        result1 = qc.compensate(Query('第一条第二項第三号'))
        result2 = qc.compensate(Query('同項第四号'))
        result3 = qc.compensate(Query('第二条'))
        result4 = qc.compensate(Query(''))
        result5 = qc.compensate(Query('第三項'))

        self.assertEqual('第一条', result1.get(LawHierarchy.ARTICLE))
        self.assertEqual('第二項', result1.get(LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', result1.get(LawHierarchy.ITEM))

        self.assertEqual('第一条', result2.get(LawHierarchy.ARTICLE))
        self.assertEqual('第二項', result2.get(LawHierarchy.PARAGRAPH))
        self.assertEqual('第四号', result2.get(LawHierarchy.ITEM))

        self.assertEqual('第二条', result3.get(LawHierarchy.ARTICLE))
        self.assertEqual('第一項', result3.get(LawHierarchy.PARAGRAPH))
        self.assertFalse(result3.has(LawHierarchy.ITEM))

        self.assertEqual('第二条', result4.get(LawHierarchy.ARTICLE))
        self.assertEqual('第一項', result4.get(LawHierarchy.PARAGRAPH))
        self.assertFalse(result4.has(LawHierarchy.ITEM))

        self.assertEqual('第二条', result5.get(LawHierarchy.ARTICLE))
        self.assertEqual('第三項', result5.get(LawHierarchy.PARAGRAPH))
        self.assertFalse(result5.has(LawHierarchy.ITEM))

    def test_compensate_fail(self):
        qc = QueryCompensator()
        with self.assertRaises(ValueError):
            qc.compensate(Query('同条中第三項'))
