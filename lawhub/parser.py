import re
from logging import getLogger

from lawhub.action import line_to_action_nodes, AddLawAction
from lawhub.law import line_to_law_node, LawTreeBuilder, LawHierarchy

LOGGER = getLogger(__name__)


class GianParser:
    def __init__(self, lines):
        self.lines = lines
        self.lines_and_nodes = []

        self._builder = LawTreeBuilder()
        self._cursor = len(self.lines) - 1
        self._cursor_flushed = self._cursor + 1

        self.success_count = 0

    def _flush_lines(self, cursor):
        """
        flush lines from until given cursor
        """

        LOGGER.debug(f'flush {self._cursor_flushed - cursor} lines')
        self.lines_and_nodes += reversed(self.lines[cursor:self._cursor_flushed])
        self._cursor_flushed = cursor
        return True

    def _flush_builder(self, actions):
        """
        flush law_tree_builder
        """

        success = False
        if len(actions) > 0 and isinstance(actions[-1], AddLawAction):
            try:
                actions[-1].law = self._builder.build()  # ToDo: validate law with "what" attribute
            except ValueError as e:
                LOGGER.debug(f'failed to build LawNodes at {self._cursor} (line={self.lines[self._cursor]})', e)
            else:
                self.success_count += self._cursor_flushed - (self._cursor + 1)
                self._cursor_flushed = self._cursor + 1
                success = True
        self._builder = LawTreeBuilder()
        return success

    def parse(self):
        """
        Convert lines to LawNodes and ActionNodes.

        Lines that are not converted will be returned as raw String
        """

        while self._cursor >= 0:
            line = self.lines[self._cursor]
            maybe_law_node = line_to_law_node(line)
            if maybe_law_node:
                law_node = maybe_law_node
                if law_node.hierarchy == LawHierarchy.ARTICLE:
                    # ToDo: Improve LawTreeBuilder to natively handle ArticleCaption in the previous line
                    match = re.fullmatch(r'（.+）', self.lines[self._cursor - 1].strip())
                    if match:
                        law_node.caption = match.group()
                        self._cursor -= 1
                try:
                    self._builder.add(law_node)
                except ValueError as e:
                    LOGGER.debug(f'failed to add LawNodes at {self._cursor} (line={line})', e)
                    self._flush_lines(self._cursor)
            else:
                action_nodes, pc, sc = line_to_action_nodes(line, meta={'line': self._cursor})
                success = self._flush_builder(action_nodes)
                if not success:
                    self._flush_lines(self._cursor + 1)
                self.lines_and_nodes += reversed(action_nodes)  # ToDo: remove AddLawAction in the middle
                if pc == sc:
                    self.success_count += 1
                    self._cursor_flushed = self._cursor
                else:
                    LOGGER.debug(f'failed to parse {pc - sc}/{pc} ActionNodes at {self._cursor} (line={self.lines[self._cursor]})')
                    self._flush_lines(self._cursor)
            self._cursor -= 1
        self._flush_lines(0)
        return self.lines_and_nodes[::-1]
