from functools import lru_cache
from typing import Callable

from fdom.astparser import make_key, parse_keyed_template_as_ast
from fdom.fdomcompiler import FdomCompiler
from fdom.taglib import Chunk, Thunk, convert_to_proposed_scheme


@lru_cache
def compile_template(*keyed_args) -> Callable:
    ast = parse_keyed_template_as_ast(*keyed_args)
    print('Compiling...')
    return FdomCompiler()(ast)


def html(*args: Chunk | Thunk) -> str:
    args = convert_to_proposed_scheme(*args)
    keyed_args = make_key(*args)
    compiled_template = compile_template(*keyed_args)
    return compiled_template(args)
