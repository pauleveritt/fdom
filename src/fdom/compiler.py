from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from functools import lru_cache
from html.parser import HTMLParser
from typing import Any, Callable, NamedTuple

from tagstr.taglib import decode_raw, Thunk


# AST model
# FIXME add constraints to this model to capture <{tag}>...</{tag}>, it must be equal


class Interpolation(NamedTuple):
    index: int  # index into the *args
    conv: str | None
    formatspec: str | None


Children = list[str, "Tag", Interpolation]
Attrs = dict[str, Any]


@dataclass
class Tag:
    tagname: str | Interpolation = None
    attrs: Attrs | Interpolation = field(default_factory=dict)
    children: Children = field(default_factory=list)


# NOTE treating Chunk and Thunk equivalent to str and tuple is WRONG - but but but it's fine for now
# given Chunk is-a str, and Thunk is-a tuple
# and a raw string is just a string that only requires decoding in *some* cases

Chunk = str  # WRONG!!! but works for our demo purposes

def make_key(*args: Chunk | Thunk) -> tuple[Chunk | tuple, ...]:
    key_args = []
    for arg in args:
        match arg:
            case Chunk():
                key_args.append(arg)
            case Thunk((_, _, conv, formatspec)) as t:
                key_args.append((None, None, conv, formatspec))
    return tuple(key_args)


def parse_template_as_ast(*args: str | Thunk) -> Tag:
    parser = ASTParser()
    for i, arg in enumerate(decode_raw(*args)):
        parser.feed(i, arg)
    return parser.result()


# generalize the below so that it build out tag functions that combine
# caching, compiler, and "runtime" (vdom, etc)


@lru_cache
def compile_it(*keyed_args) -> Callable:
    # Returns a "partial" function that parses Chunks in keyed_args,
    # plus any interpretation needed for (conv, formatspec), if any;
    # this partial function can then be applied to the usual *args

    # This partial function is compiled with respect to the source HTML
    # in the chunks such that any parsing is done once; and it can build
    # the desired output format, like FDOM or VDOM.

    # Need to figure out specifically how to make this part pluggable, but should be
    # straightforward.

    # (I claim this is comparable to functools.partial, even though it
    # takes the same signature as the tag function because it ignores the
    # chunks, for convenience sake, and only applies the interpolations
    # from the thunks)
    return VDOMCompiler()(parse_template_as_ast(*keyed_args))


def html(*args: str | Thunk):
    # applies the partial function to the args, per above -
    # as noted above, only the interpolations from the thunks now matter here
    return compile_it(*make_key(*args))(vdom, *args)


# Q: PEP8 tag_name instead tagName
# Q: Return either a namedtuple or a typed dict
def vdom(tagName: str, attributes: dict | None, children: list | None) -> dict:
    d = {"tagName": tagName}
    if attributes:
        d["attributes"] = attributes
    if children:
        d["children"] = children
    return d


class BaseCompiler:
    # Q: Need to initialize "lines", what's the typing?
    def __init__(self, indent=2, name="compiled"):
        self.indent = indent
        self.name = name

    @property
    def code(self) -> str:
        return "\n".join(self.lines)

    def add_line(self, level, line):
        indentation = " " * self.indent * (level + 1)
        self.lines.append(f"{indentation}{line}")

    def __call__(self, tag: Tag) -> Callable:
        self.compile(tag)
        print(self.code)

        # standard boilerplate to compile a string into a callable
        code_obj = compile(self.code, "<string>", "exec")
        captured = {}
        exec(code_obj, captured)
        return captured["compiled"]


class VDOMCompiler(BaseCompiler):
    def __init__(self, indent=2, name="compiled"):
        self.lines = [f"def {name}(vdom, /, *args):", "  return \\"]
        super().__init__()

    def compile(self, tag: Tag, level=0):
        # tagname
        match tag:
            case Tag(Interpolation() as i, _, _):
                # interpolate getvalue() for the tagname - assume vdom checks as valid when rendered
                self.add_line(level, f"vdom(")
                self.add_line(level + 1, f"args[{i.index}][0](), ")
            case Tag(None, _, _):
                pass
            case Tag(str() as name, _, _):
                self.add_line(level, f"vdom({name!r}, ")
            case _:
                raise Exception(f"Expected match {tag=}")

        # attrs
        match tag:
            case Tag(_, Interpolation() as i, _):
                self.add_line(level + 1, f"args[{i.index}][0](), ")
            case Tag(_, dict() as d):
                self.add_line(level + 1, f"{d!r}, ")

        # children
        self.add_line(level + 1, "[")
        for child in tag.children:
            match child:
                case Tag() as t:
                    # explicit recursive case
                    self.compile(t, level + 2)
                case Interpolation() as i:
                    # implicit recursive case - calling this interpolation will result in more children
                    # should presumably do some checking
                    self.add_line(level + 2, f"args[{i.index}][0](), ")
                case str() as s:
                    self.add_line(level + 2, f"{s!r}, ")
        self.add_line(level + 1, "])")


# We choose this symbol because, after replacing all $ with $$, there is no way for a
# user to feed a string that would result in x$x. Thus we can reliably split an HTML
# data string on x$x. We also choose this because, the HTML parse looks for tag names
# begining with the regex pattern '[a-zA-Z]'.
PLACEHOLDER = "x$x"


def escape_placeholder(string: str) -> str:
    return string.replace("$", "$$")


def unescape_placeholder(string: str) -> str:
    return string.replace("$$", "$")


class ASTParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Tag()
        self.stack: list[Tag] = [self.root]
        self.interpolations: deque[Interpolation] = deque()

    def feed(self, index: int, data: str | Thunk) -> None:
        match data:
            case str():
                super().feed(escape_placeholder(data))
            case _, _, conv, formatspec:
                self.interpolations.append(Interpolation(index, conv, formatspec))
                super().feed(PLACEHOLDER)

    def result(self) -> Tag:
        root = self.root
        self.close()
        match root.children:
            case []:
                raise ValueError("Nothing to return")
            case [child]:
                return child
            case _:
                return self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == PLACEHOLDER:
            tag = self.interpolations.popleft()

        node_attrs = {}
        for k, v in attrs:
            if k == PLACEHOLDER and v is None:
                node_attrs = self.interpolations.popleft()
            elif PLACEHOLDER in k:
                raise SyntaxError("Cannot interpolate attribute names")
            elif v == PLACEHOLDER:
                node_attrs[k] = self.interpolations.popleft()

        # At this point all interpolated values should have been consumed.
        # assert not self.interpolations, "Did not interpolate all values"

        this_node = Tag(tag, node_attrs)
        last_node = self.stack[-1]
        last_node.children.append(this_node)
        self.stack.append(this_node)

    def handle_data(self, data: str) -> None:
        children = self.stack[-1].children
        if data == PLACEHOLDER:
            parts = [data]
        else:
            parts = data.split(PLACEHOLDER)

        for part in parts:
            if part == "" or part == PLACEHOLDER:
                children.append(self.interpolations.popleft())
            else:
                children.append(part)

    def handle_endtag(self, tag: str) -> None:
        node = self.stack.pop()

        # FIXME should also handle a tag with a placeholder in it, similar to handle_data

        if tag == PLACEHOLDER:
            # this should add a constraint to the returned AST such that these two placeholders must equal
            self.interpolations.popleft()
            return None

        # At this point all interpolated values should have been consumed.
        # assert not self.values, "Did not interpolate all values"

        if tag is ...:
            # handle end tag shorthand
            return None

        if tag != node.tagname:
            raise SyntaxError(
                "Start tag {node.tag!r} does not match end tag {interp_tag!r}"
            )
