from unittest import TestCase

from lawhub.law import LawHierarchy
from lawhub.query import QueryType, Query, QueryCompensator


class TestQuery(TestCase):
    def test_init_at_hierarchy(self):
        text = '第一条第二項第三号'
        query = Query(text)

        self.assertEqual(QueryType.AT_HIERARCHY, query.query_type)
        self.assertEqual('第一条', query.get(LawHierarchy.ARTICLE))
        self.assertEqual('第二項', query.get(LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', query.get(LawHierarchy.ITEM))

    def test_init_after_word(self):
        text = '第一条第二項第三号中「文字列」の下'
        query = Query(text)

        self.assertEqual(QueryType.AFTER_WORD, query.query_type)
        self.assertEqual('第一条', query.get(LawHierarchy.ARTICLE))
        self.assertEqual('第二項', query.get(LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', query.get(LawHierarchy.ITEM))
        self.assertEqual('文字列', query.word)

    def test_init_after_hierarchy(self):
        text = '第一条第二項第三号の次'
        query = Query(text)

        self.assertEqual(QueryType.AFTER_HIERARCHY, query.query_type)
        self.assertEqual('第一条', query.get(LawHierarchy.ARTICLE))
        self.assertEqual('第二項', query.get(LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', query.get(LawHierarchy.ITEM))

    # def test_init_multiple_fail(self):
    #     text = '第一条及び第二条'
    #     with self.assertRaises(NotImplementedError):
    #         Query(text)


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
