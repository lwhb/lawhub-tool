import itertools
from logging import getLogger

from lawhub.action import line_to_action_nodes, AddLawAction
from lawhub.kanzize import kanji2int
from lawhub.law import line_to_law_node, LawTreeBuilder, LawHierarchy

LOGGER = getLogger(__name__)


class ParseResultEntry:
    def __init__(self, nodes, lines, idx_start, idx_end, success):
        assert len(lines) == idx_end - idx_start
        self.nodes = nodes
        self.lines = lines
        self.idx_start = idx_start
        self.idx_end = idx_end
        self.success = success

    def __str__(self):
        ss = []
        if not self.success:
            for line in self.lines:
                ss.append(f'!!{line}')
        for node in self.nodes:
            ss.append(node.serialize())
        return '\n'.join(ss)

    @classmethod
    def from_line(cls, line, idx):
        try:
            return LawParseResultEntry.from_line(line, idx)
        except ValueError:
            return ActionParseResultEntry.from_line(line, idx)

    @staticmethod
    def merge_law_entries(entries):
        assert len(entries) > 0
        assert sum(map(lambda e: isinstance(e, LawParseResultEntry), entries)) == len(entries)

        nodes = list(itertools.chain.from_iterable(map(lambda e: e.nodes, entries)))
        lines = list(itertools.chain.from_iterable(map(lambda e: e.lines, entries)))
        idx_start = entries[0].idx_start
        idx_end = entries[-1].idx_end
        try:
            builder = LawTreeBuilder()
            for node in nodes[::-1]:
                builder.add(node)
            merged_nodes = builder.build()
        except ValueError:
            LOGGER.warning(f'failed to build law tree')
            return LawParseResultEntry(nodes=nodes, lines=lines, idx_start=idx_start, idx_end=idx_end, success=False)
        else:
            return LawParseResultEntry(nodes=merged_nodes, lines=lines, idx_start=idx_start, idx_end=idx_end, success=True)

    @staticmethod
    def merge_add_law_action(action_entry, law_entry):
        assert isinstance(action_entry, ActionParseResultEntry)
        assert isinstance(law_entry, LawParseResultEntry)

        lines = action_entry.lines + law_entry.lines
        idx_start = action_entry.idx_start
        idx_end = law_entry.idx_end
        try:
            ParseResultEntry._validate_add_law_action_pair(action_entry, law_entry)
        except ValueError:
            return ParseResultEntry(nodes=action_entry.nodes + law_entry.nodes, lines=lines, idx_start=idx_start, idx_end=idx_end, success=False)
        else:
            action_entry.nodes[-1].law = law_entry.nodes
            return ActionParseResultEntry(nodes=action_entry.nodes, lines=lines, idx_start=idx_start, idx_end=idx_end, success=action_entry.success)

    @staticmethod
    def _validate_add_law_action_pair(action_entry, law_entry):
        if not(action_entry.nodes and isinstance(action_entry.nodes[-1], AddLawAction)):
            raise ValueError('last action node is not AddLawAction')
        what = action_entry.nodes[-1].what
        try:
            count = kanji2int(what[:-1])
            hierarchy = LawHierarchy(what[-1])
        except ValueError as e:
            raise ValueError(f'invalid AddLawAction.what string: "{what}"') from e
        if not(len(law_entry.nodes) == count and sum(map(lambda n: n.hierarchy == hierarchy, law_entry.nodes))):
            raise ValueError(f'law entry does not match with ({count}, {hierarchy})')
        return True


class LawParseResultEntry(ParseResultEntry):
    @classmethod
    def from_line(cls, line, idx):
        maybe_law_node = line_to_law_node(line)
        if maybe_law_node:
            return cls(nodes=[maybe_law_node], lines=[line], idx_start=idx, idx_end=idx + 1, success=True)
        else:
            raise ValueError('failed to instantiate LawParseResultEntry')


class ActionParseResultEntry(ParseResultEntry):
    @classmethod
    def from_line(cls, line, idx):
        action_nodes, pc, sc = line_to_action_nodes(line, meta={'line': idx})
        return cls(nodes=action_nodes, lines=[line], idx_start=idx, idx_end=idx + 1, success=(pc == sc))


class GianParser:
    def parse(self, lines):
        parse_result = []
        for idx, line in enumerate(lines):
            parse_result.append(ParseResultEntry.from_line(line, idx))
        parse_result = self._find_and_merge_law_entries(parse_result)
        parse_result = self._find_and_merge_add_law_actions(parse_result)
        return parse_result

    def _find_and_merge_law_entries(self, entries):
        result = list()
        buffer = list()
        for entry in entries:
            if isinstance(entry, LawParseResultEntry):
                buffer.append(entry)
            else:
                if buffer:
                    result.append(ParseResultEntry.merge_law_entries(buffer))
                    buffer = list()
                result.append(entry)
        if buffer:
            result.append(ParseResultEntry.merge_law_entries(buffer))
        return result

    def _find_and_merge_add_law_actions(self, entries):
        result = list()
        idx = 0
        while idx < len(entries):
            entry = entries[idx]
            idx += 1
            if isinstance(entry, ActionParseResultEntry) and entry.nodes and isinstance(entry.nodes[-1], AddLawAction):
                law_entry = entries[idx]  # can be empty when reached to end
                idx += 1
                merged_entry = ParseResultEntry.merge_add_law_action(entry, law_entry)
                result.append(merged_entry)
            else:
                result.append(entry)
        return result
