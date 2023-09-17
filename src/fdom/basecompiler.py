from functools import lru_cache
from textwrap import dedent
from typing import Callable

from fdom.astparser import make_key, parse_keyed_template_as_ast, Tag
from fdom.taglib import Chunk, Thunk, convert_to_proposed_scheme


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
        print("Compiled code:\n", self.code)

        # standard boilerplate to compile a string into a callable
        code_obj = compile(self.code, "<string>", "exec")
        captured = {}
        exec(code_obj, captured)
        return captured[self.name]
