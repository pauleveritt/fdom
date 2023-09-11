from functools import lru_cache
from textwrap import dedent
from typing import Callable

from fdom.astparser import make_key, parse_keyed_template_as_ast, Tag
from fdom.taglib import Chunk, Thunk, convert_to_proposed_scheme

# FIXME make this a decorator, so that it can be applied more generally

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
    ast = parse_keyed_template_as_ast(*keyed_args)
    print("AST:\n", ast)
    return VDOMCompiler()(ast)


def make_html_tag(*args: Chunk | Thunk):
    # applies the partial function to the args, per above -
    # as noted above, only the interpolations from the thunks now matter
    # here
    args = convert_to_proposed_scheme(*args)
    return compile_it(*make_key(*args))(vdom, *args)


class BaseCompiler:
    def __init__(self, indent: int = 2, name: str = "compiled"):
        self.indent: int = indent
        self.name: str = name
        self.lines: list[str] = dedent(self.preamble).split('\n')

    @property
    def code(self) -> str:
        return "\n".join(self.lines)

    def add_line(self, level, line):
        indentation = " " * self.indent * (level + 1)
        self.lines.append(f"{indentation}{line}")

    def __call__(self, tag: Tag) -> Callable:
        self.compile(tag)
        # print("Compiled code:\n", self.code)

        # standard boilerplate to compile a string into a callable
        code_obj = compile(self.code, "<string>", "exec")
        captured = {}
        exec(code_obj, captured)
        return captured[self.name]
