from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Literal, NamedTuple

from fdom.thunky import Chunk, Thunk, convert_to_proposed_scheme

"""
Supports parsing HTML templates with interpolations that can be arbitrarily placed:

Tag names can contain arbitrary interpolations, such as <h{level}> or <My{custom}{element}Name>;
see https://lit.dev/docs/templates/expressions/#static-expressions for a comparable idea in Lit.

Attributes can be static, or usng interpolations. Rendering (not handled by the
parser) should be based on HTML tag semantics:

on{action}=foo
{attrs}  #
style={style}  # renders to CSS format
disabled={disabled}  # True renders to 'disabled', False to elided

NOTE It is possible that we would want to support the expression text
{disabled}  # the name is meaningful

# FIXME add constraint nodes to the resulting parse to capture for example
# <{tag}>...</{tag}>, that they must be equal.
"""


class Interpolation(NamedTuple):
    index: int  # index into the *args
    conv: str | None
    formatspec: str | None


# FIXME there must be a better name for this. Elements? Expando?

E = list[str, Interpolation]

@dataclass
class Tag:
    tagname: E = None
    attrs: list[tuple[E, E | None]] = field(default_factory=list)
    children: list[str, Interpolation, 'Tag'] = field(default_factory=list)


# Normalizes thunks such that they are suitable for keys, that is regardless of
# getvalue, text, we only care about conv, formatspec.

class KeyThunk(NamedTuple):
    conv: Literal['a', 'r', 's'] | None = None
    formatspec: str | None = None


def make_key(*args: Chunk | Thunk) -> tuple[Chunk | KeyThunk, ...]:
    args = convert_to_proposed_scheme(*args)
    key_args = []
    for arg in args:
        match arg:
            case Chunk():
                key_args.append(arg)
            case Thunk() as t:
                key_args.append(KeyThunk(t.conv, t.formatspec))
    return tuple(key_args)


def parse_keyed_template_as_ast(*args: Chunk | KeyThunk) -> Tag:
    parser = ASTParser()
    for i, arg in enumerate(args):
        parser.feed(i, arg)
    return parser.result()


def as_ast(*args: Chunk | Thunk) -> Tag:
    """Convenience function, suitable for using as a tag function"""
    args = convert_to_proposed_scheme(*args)
    return parse_keyed_template_as_ast(*make_key(*args))


# We choose this symbol because, after replacing all $ with $$, there is no way for a
# user to feed a string that would result in x$x. Thus we can reliably split an HTML
# data string on x$x. We also choose this because, the HTML parse looks for tag names
# beginning with the regex pattern '[a-zA-Z]'.
PLACEHOLDER = 'x$x'


def escape_placeholder(string: str) -> str:
    return string.replace('$', '$$')


def unescape_placeholder(string: str) -> str:
    return string.replace('$$', '$')


def is_static_element(tagname: E) -> bool:
    match tagname:
        case [str()]:
            return True
        case _:
            return False


class ASTParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Tag()
        self.stack: list[Tag] = [self.root]
        self.interpolations: deque[Interpolation] = deque()

    def feed(self, index: int, data: Chunk | KeyThunk) -> None:
        match data:
            case Chunk() as c:
                super().feed(escape_placeholder(c.decoded))
            case KeyThunk() as t:
                self.interpolations.append(Interpolation(index, t.conv, t.formatspec))
                super().feed(PLACEHOLDER)

    def result(self) -> Tag:
        self.close()
        match self.root.children:
            case []:
                raise ValueError('Nothing to return')
            case [child]:
                return child
            case _:
                return self.root

    def expand_interpolations(self, s: str | None) -> E | None:
        if s is None:
            return None
        elif s == PLACEHOLDER:
            return [self.interpolations.popleft()]

        expanded = []
        split = s.split(PLACEHOLDER)
        for i, item in enumerate(split):
            if item == '':
                expanded.append(self.interpolations.popleft())
            else:
                expanded.append(unescape_placeholder(item))
                if i != len(split) - 1:
                    expanded.append(self.interpolations.popleft())
        return expanded

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        expanded_tagname = self.expand_interpolations(tag)
        expanded_attrs = []
        for k, v in attrs:
            expanded_attrs.append((self.expand_interpolations(k), self.expand_interpolations(v)))

        # At this point all interpolated values should have been consumed, and therefore a bug in this class.
        assert not self.interpolations, 'Did not interpolate all values'

        this_node = Tag(expanded_tagname, expanded_attrs)
        last_node = self.stack[-1]
        last_node.children.append(this_node)
        self.stack.append(this_node)

    def handle_data(self, data: str) -> None:
        children = self.stack[-1].children
        children.extend(self.expand_interpolations(data))

    def handle_endtag(self, tag: str) -> None:
        node = self.stack.pop()
        expanded_tagname = self.expand_interpolations(tag)

        if is_static_element(expanded_tagname) and is_static_element(node.tagname):
            if expanded_tagname != node.tagname:
                raise ValueError(f'Start tag {node.tagname[0]!r} does not match end tag {expanded_tagname[0]!r}')
        # FIXME otherwise handle as a constraint - this needs to be added to the parsed result

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # handle specially because the starttag had previously done all expansions, so no need to repeat
        self.handle_starttag(tag, attrs)
        self.handlenode = self.stack.pop()
