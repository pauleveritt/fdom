from functools import partial
from typing import Any, Callable, Literal

from fdom.taglib import convert_to_proposed_scheme, Conversion, Chunk, Thunk


def make_template(tag: Callable, template: str) -> Callable:
    def identity(*args):
        return args

    # should do a gensym here to ensure what we call
    # extract_tag, f are unique (and not in use by the template)
    namespace = {'extract_tag': identity, 'f': None}
    escaped_template = template.replace("'", r"\'")
    print(f'{escaped_template=}')

    # do a first pass to extract any used names
    used_names = set()
    args = eval(f"extract_tag'{escaped_template}'", None, namespace)
    for arg in args:
        match arg:
            case getvalue, _, _, _:
                used_names |= set(getvalue.__code__.co_names)

    # then build a wrapper function for the template
    param_names = used_names - globals().keys()
    params = ', '.join(sorted(param_names))
    code = f"""
def f(tag, {params}):
    return tag'{escaped_template}'
"""
    print(f'{code=}')
    code_obj = compile(code, '<string>', 'exec')
    exec(code_obj, None, namespace)
    return partial(namespace['f'], tag=tag)


def convert(value: Any, conv: Conversion) -> str:
    match conv:
        case 'a':
            return ascii(value)
        case 'r':
            return repr(value)
        case 's' | None:
            return str(value)


def my_fstring(*args: Chunk | Thunk) -> str:
    args = convert_to_proposed_scheme(*args)
    x = []
    for arg in args:
        match arg:
            case Chunk() as chunk:
                x.append(chunk.decoded)
            case Thunk() as thunk:
                formatspec = '' if thunk.formatspec is None else thunk.formatspec
                x.append(convert(format(thunk.getvalue(), formatspec), thunk.conv))
    return ''.join(x)


def test_template():
    template = make_template(my_fstring, "{alice}, you should meet {bob}, he's my friend too!")
    assert template(alice='Alice', bob='Bob') == "Alice, you should meet Bob, he's my friend too!"
