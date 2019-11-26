from unittest import TestCase

from lawhub.law import LawHierarchy
from lawhub.query import Query, QueryCompensator


class TestQuery(TestCase):
    def test_query(self):
        text = '第一条第一項第一号'
        query = Query(text)

        self.assertEqual('第一条', query.get(LawHierarchy.ARTICLE))
        self.assertEqual('第一項', query.get(LawHierarchy.PARAGRAPH))
        self.assertEqual('第一号', query.get(LawHierarchy.ITEM))


class TestQueryCompensator(TestCase):
    def test_compensate_success(self):
        qc = QueryCompensator()
        result1 = qc.compensate(Query('第一条第一号'))
        result2 = qc.compensate(Query('同条中第三号'))
        result3 = qc.compensate(Query('第二条'))
        result4 = qc.compensate(Query('第二号'))

        self.assertEqual(result1.get(LawHierarchy.ARTICLE), '第一条')
        self.assertFalse(result1.has(LawHierarchy.PARAGRAPH))
        self.assertTrue(result1.get(LawHierarchy.ITEM), '第一号')

        self.assertEqual(result2.get(LawHierarchy.ARTICLE), '第一条')
        self.assertFalse(result2.has(LawHierarchy.PARAGRAPH))
        self.assertTrue(result2.get(LawHierarchy.ITEM), '第三号')

        self.assertEqual(result3.get(LawHierarchy.ARTICLE), '第二条')
        self.assertFalse(result3.has(LawHierarchy.PARAGRAPH))
        self.assertFalse(result3.has(LawHierarchy.ITEM))

        self.assertEqual(result4.get(LawHierarchy.ARTICLE), '第二条')
        self.assertFalse(result4.has(LawHierarchy.PARAGRAPH))
        self.assertEqual(result4.get(LawHierarchy.ITEM), '第二号')

    def test_compensate_fail(self):
        qc = QueryCompensator()
        with self.assertRaises(ValueError):
            qc.compensate(Query('同条中第三項'))
