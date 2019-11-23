from unittest import TestCase

from lawhub.query import Query, QueryCompensator, LawDivision, extract_law_division


class TestQuery(TestCase):
    def test_extract_law_division(self):
        string = '同条中第一項第一号'

        self.assertEqual('同条', extract_law_division(string, LawDivision.JOU))
        self.assertEqual('第一項', extract_law_division(string, LawDivision.KOU))
        self.assertEqual('第一号', extract_law_division(string, LawDivision.GOU))


class TestQueryCompensator(TestCase):
    def test_compensate_success(self):
        qc = QueryCompensator()
        result1 = qc.compensate(Query('第一条第一項'))
        result2 = qc.compensate(Query('同条中第三項'))
        result3 = qc.compensate(Query('第二条'))
        result4 = qc.compensate(Query('第二項'))

        self.assertEqual(result2.get(LawDivision.JOU), '第一条')
        self.assertEqual(result4.get(LawDivision.JOU), '第二条')

    def test_compensate_fail(self):
        qc = QueryCompensator()
        result = qc.compensate(Query('同条中第三項'))
        self.assertFalse(result.has(LawDivision.JOU))
        self.assertTrue(result.has(LawDivision.KOU))
