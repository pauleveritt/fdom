from functools import lru_cache
from typing import Callable, Iterable

from fdom.astparser import make_key, parse_keyed_template_as_ast
from fdom.htmlcompiler import HTMLCompiler, HTML
from fdom.taglib import Chunk, Thunk, convert_to_proposed_scheme


@lru_cache
def compile_template(*keyed_args) -> Callable:
    ast = parse_keyed_template_as_ast(*keyed_args)
    print('Compiling...')
    return HTMLCompiler()(ast)


def html(*args: Chunk | Thunk) -> str:
    args = convert_to_proposed_scheme(*args)
    keyed_args = make_key(*args)
    compiled_template = compile_template(*keyed_args)
    return HTML(''.join(compiled_template(args)))


def html_iter(*args: Chunk | Thunk) -> Iterable[str]:
    args = convert_to_proposed_scheme(*args)
    keyed_args = make_key(*args)
    compiled_template = compile_template(*keyed_args)
    return iter(compiled_template(args))
