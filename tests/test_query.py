from unittest import TestCase

from lawhub.law import LawHierarchy
from lawhub.query import Query, QueryCompensator


class TestQuery(TestCase):
    def test_query(self):
        text = '第一条第二項第三号'
        query = Query(text)

        self.assertEqual('第一条', query.get(LawHierarchy.ARTICLE))
        self.assertEqual('第二項', query.get(LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', query.get(LawHierarchy.ITEM))


class TestQueryCompensator(TestCase):
    def test_compensate_success(self):
        qc = QueryCompensator()
        result1 = qc.compensate(Query('第一条第二項第三号'))
        result2 = qc.compensate(Query('同項第四号'))
        result3 = qc.compensate(Query('第二条'))
        result4 = qc.compensate(Query('第三項'))

        self.assertEqual(result1.get(LawHierarchy.ARTICLE), '第一条')
        self.assertEqual(result1.get(LawHierarchy.PARAGRAPH), '第二項')
        self.assertEqual(result1.get(LawHierarchy.ITEM), '第三号')

        self.assertEqual(result2.get(LawHierarchy.ARTICLE), '第一条')
        self.assertEqual(result2.get(LawHierarchy.PARAGRAPH), '第二項')
        self.assertEqual(result2.get(LawHierarchy.ITEM), '第四号')

        self.assertEqual(result3.get(LawHierarchy.ARTICLE), '第二条')
        self.assertEqual(result3.get(LawHierarchy.PARAGRAPH), '第一項')
        self.assertFalse(result3.has(LawHierarchy.ITEM))

        self.assertEqual(result4.get(LawHierarchy.ARTICLE), '第二条')
        self.assertEqual(result4.get(LawHierarchy.PARAGRAPH), '第三項')
        self.assertFalse(result4.has(LawHierarchy.ITEM))

    def test_compensate_fail(self):
        qc = QueryCompensator()
        with self.assertRaises(ValueError):
            qc.compensate(Query('同条中第三項'))
