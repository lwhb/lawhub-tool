import itertools
from logging import getLogger

from lawhub.action import line_to_action_nodes, AddLawAction
from lawhub.kanzize import kanji2int
from lawhub.law import line_to_law_node, LawTreeBuilder, LawHierarchy, Article

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
        for c in [RevisionParseResultEntry,
                  LawParseResultEntry,
                  ActionParseResultEntry]:
            try:
                return c.from_line(line, idx)
            except ValueError:
                pass
        raise ValueError(f'failed to instantiate ParseResultEntry from "{line}"')

    @staticmethod
    def merge_revision_caption(caption_entry, revision_entry):
        assert isinstance(caption_entry, LawParseResultEntry)
        assert isinstance(revision_entry, RevisionParseResultEntry)

        lines = caption_entry.lines + revision_entry.lines
        idx_start = caption_entry.idx_start
        idx_end = revision_entry.idx_end

        revision_entry.nodes[0].caption = caption_entry.nodes[0].caption
        return RevisionParseResultEntry(nodes=revision_entry.nodes, lines=lines, idx_start=idx_start, idx_end=idx_end, success=True)

    @staticmethod
    def merge_law_entries(entries):
        assert len(entries) > 0
        assert sum(map(lambda entry: isinstance(entry, LawParseResultEntry), entries)) == len(entries)

        nodes = list(itertools.chain.from_iterable(map(lambda entry: entry.nodes, entries)))
        lines = list(itertools.chain.from_iterable(map(lambda entry: entry.lines, entries)))
        idx_start = entries[0].idx_start
        idx_end = entries[-1].idx_end
        try:
            builder = LawTreeBuilder()
            for node in nodes[::-1]:
                builder.add(node)
            merged_nodes = builder.build()
        except ValueError as e:
            LOGGER.exception(f'failed to merge law entries from "{lines[0]}" to "{lines[-1]}"')
            return LawParseResultEntry(nodes=nodes, lines=lines, idx_start=idx_start, idx_end=idx_end, success=False)
        else:
            return LawParseResultEntry(nodes=merged_nodes, lines=lines, idx_start=idx_start, idx_end=idx_end, success=True)

    @staticmethod
    def merge_add_law_action(action_entry, law_entry):
        lines = action_entry.lines + law_entry.lines
        idx_start = action_entry.idx_start
        idx_end = law_entry.idx_end
        try:
            ParseResultEntry._validate_add_law_action_pair(action_entry, law_entry)
        except ValueError as e:
            LOGGER.exception(f'failed to merge add law action from "{lines[0]}" to "{lines[-1]}"')
            return ParseResultEntry(nodes=action_entry.nodes + law_entry.nodes, lines=lines, idx_start=idx_start, idx_end=idx_end, success=False)
        else:
            action_entry.nodes[-1].law = law_entry.nodes
            return ActionParseResultEntry(nodes=action_entry.nodes, lines=lines, idx_start=idx_start, idx_end=idx_end, success=action_entry.success)

    @staticmethod
    def _validate_add_law_action_pair(action_entry, law_entry):
        if not (isinstance(action_entry, ActionParseResultEntry)):
            raise ValueError(f'invalid action entry type: {type(action_entry)}')
        if not (isinstance(law_entry, LawParseResultEntry)):
            raise ValueError(f'invalid law entry type: {type(law_entry)}')
        if not (action_entry.nodes and isinstance(action_entry.nodes[-1], AddLawAction)):
            raise ValueError('last action node is not AddLawAction')
        what = action_entry.nodes[-1].what
        try:
            if what == '各号':
                count = len(law_entry.nodes)
                hierarchy = LawHierarchy.ITEM
            else:
                count = kanji2int(what[:-1])
                hierarchy = LawHierarchy(what[-1])
        except ValueError as e:
            raise ValueError(f'invalid AddLawAction.what string: "{what}"') from e  # ToDo: support 及び
        if not (len(law_entry.nodes) == count and sum(map(lambda n: n.hierarchy == hierarchy, law_entry.nodes))):
            raise ValueError(f'law entry does not match with ({count}, {hierarchy}): {";".join(map(lambda n: n.hierarchy.name, law_entry.nodes))}')
        return True


class RevisionParseResultEntry(ParseResultEntry):
    @classmethod
    def from_line(cls, line, idx):
        if line.strip().endswith('次のように改正する。'):
            # add article title if necessary
            maybe_title = line.strip().split()[0]
            if not (LawHierarchy.ARTICLE.extract(maybe_title, allow_partial_match=False, allow_placeholder=False)):
                line = '第一条 ' + line
            maybe_node = line_to_law_node(line)
            if maybe_node:
                return cls(nodes=[maybe_node], lines=[line], idx_start=idx, idx_end=idx + 1, success=True)
        raise ValueError(f'failed to instantiate {cls.__name__}')


class LawParseResultEntry(ParseResultEntry):
    @classmethod
    def from_line(cls, line, idx):
        maybe_law_node = line_to_law_node(line)
        if maybe_law_node:
            return cls(nodes=[maybe_law_node], lines=[line], idx_start=idx, idx_end=idx + 1, success=True)
        else:
            raise ValueError(f'failed to instantiate {cls.__name__}')


class ActionParseResultEntry(ParseResultEntry):
    @classmethod
    def from_line(cls, line, idx):
        action_nodes, pc, sc = line_to_action_nodes(line, meta={'line': idx})
        return cls(nodes=action_nodes, lines=[line], idx_start=idx, idx_end=idx + 1, success=(pc == sc))


class GianParser:
    def parse(self, lines):
        parse_result = list()
        for idx, line in enumerate(lines):
            parse_result.append(ParseResultEntry.from_line(line, idx))
        parse_result = self._find_and_merge_revision_entry(parse_result)
        parse_result = self._find_and_merge_law_entries(parse_result)
        parse_result = self._find_and_merge_add_law_actions(parse_result)
        return parse_result

    def _find_and_merge_revision_entry(self, entries):
        result = list()
        idx = len(entries) - 1
        while idx >= 0:
            entry = entries[idx]
            idx -= 1
            if isinstance(entry, RevisionParseResultEntry):
                prev_entry = entries[idx]
                if isinstance(prev_entry, LawParseResultEntry):
                    maybe_caption_entry = prev_entry.nodes[0]
                    if isinstance(maybe_caption_entry, Article) and maybe_caption_entry.is_caption_only():
                        result.append(ParseResultEntry.merge_revision_caption(prev_entry, entry))
                        idx -= 1
                        continue
            result.append(entry)
        return result[::-1]

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
                law_entry = entries[idx]  # can be empty when already reached to the end
                idx += 1
                merged_entry = ParseResultEntry.merge_add_law_action(entry, law_entry)
                result.append(merged_entry)
            else:
                result.append(entry)
        return result
