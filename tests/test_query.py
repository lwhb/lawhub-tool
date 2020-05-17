from unittest import TestCase

from lawhub.law import LawHierarchy
from lawhub.query import Query, QueryType, QueryCompensator
from lawhub.serializable import is_serializable


class TestQuery(TestCase):
    def test_from_text(self):
        text = '第一条第二項第三号の次'
        query = Query.from_text(text)

        self.assertEqual(text, query.text)
        self.assertEqual(QueryType.AFTER, query.query_type)
        self.assertEqual('第一条', query.get(LawHierarchy.ARTICLE))
        self.assertEqual('第二項', query.get(LawHierarchy.PARAGRAPH))
        self.assertEqual('第三号', query.get(LawHierarchy.ITEM))
        self.assertEqual('', query.get(LawHierarchy.SUBITEM1))
        self.assertTrue(is_serializable(query))
        print(query.serialize())


class TestQueryCompensator(TestCase):
    def test_compensate_success(self):
        qc = QueryCompensator()
        texts = ['附則第一条第二項第三号', 'ランダムな文', '同項第四号の次', '第二条', '', '第三項', '第一節', '同節']
        results = list(map(lambda text: qc.compensate(Query.from_text(text)), texts))

        self.assertEqual(len(texts), len(results))
        for i, result in enumerate(results):
            if i == 0:
                self.assertEqual('附則第一条第二項第三号', result.text)
                self.assertEqual('附則', result.get(LawHierarchy.SUPPLEMENT))
                self.assertEqual('第一条', result.get(LawHierarchy.ARTICLE))
                self.assertEqual('第二項', result.get(LawHierarchy.PARAGRAPH))
                self.assertEqual('第三号', result.get(LawHierarchy.ITEM))
            elif i == 1:
                self.assertEqual('ランダムな文', result.text)
                self.assertTrue(result.is_empty())
            elif i == 2:
                self.assertEqual('同項第四号の次', result.text)
                self.assertEqual(QueryType.AFTER, result.query_type)
                self.assertEqual('附則', result.get(LawHierarchy.SUPPLEMENT))
                self.assertEqual('第一条', result.get(LawHierarchy.ARTICLE))
                self.assertEqual('第二項', result.get(LawHierarchy.PARAGRAPH))
                self.assertEqual('第四号', result.get(LawHierarchy.ITEM))
            elif i == 3:
                self.assertEqual('第二条', result.text)
                self.assertEqual(QueryType.AT, result.query_type)
                self.assertEqual('附則', result.get(LawHierarchy.SUPPLEMENT))
                self.assertEqual('第二条', result.get(LawHierarchy.ARTICLE))
                self.assertFalse(result.has(LawHierarchy.PARAGRAPH))
                self.assertFalse(result.has(LawHierarchy.ITEM))
            elif i == 4:
                self.assertEqual('', result.text)
                self.assertEqual(QueryType.AT, result.query_type)
                self.assertEqual('附則', result.get(LawHierarchy.SUPPLEMENT))
                self.assertEqual('第二条', result.get(LawHierarchy.ARTICLE))
                self.assertFalse(result.has(LawHierarchy.PARAGRAPH))
                self.assertFalse(result.has(LawHierarchy.ITEM))
            elif i == 5:
                self.assertEqual('第三項', result.text)
                self.assertEqual(QueryType.AT, result.query_type)
                self.assertEqual('附則', result.get(LawHierarchy.SUPPLEMENT))
                self.assertEqual('第二条', result.get(LawHierarchy.ARTICLE))
                self.assertEqual('第三項', result.get(LawHierarchy.PARAGRAPH))
                self.assertFalse(result.has(LawHierarchy.ITEM))
            elif i == 6:
                self.assertEqual('第一節', result.text)
                self.assertEqual(QueryType.AT, result.query_type)
                self.assertEqual('附則', result.get(LawHierarchy.SUPPLEMENT))
                self.assertEqual('第一節', result.get(LawHierarchy.SECTION))
            elif i == 7:
                self.assertEqual('同節', result.text)
                self.assertEqual(QueryType.AT, result.query_type)
                self.assertEqual('附則', result.get(LawHierarchy.SUPPLEMENT))
                self.assertEqual('第一節', result.get(LawHierarchy.SECTION))

    def test_compensate_fail(self):
        qc = QueryCompensator()
        query = Query.from_text('同条中第三項')
        with self.assertRaises(ValueError):
            qc.compensate(query)
