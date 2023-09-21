from abc import abstractmethod
from collections.abc import Generator, Iterable
from html import escape
from typing import Any, Callable
import re

from fdom.astparser import E, Interpolation, Tag, is_static_element
from fdom.basecompiler import BaseCompiler
from fdom.taglib import Chunk, Conversion, Thunk


class HTMLIterator:
    @abstractmethod
    def __iter__(self):
        ...


class HTML(str):
    """Marker class for HTML content"""
    pass


attribute_name_re = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_\-\.]*$')
tagname_re = re.compile(r'^(?!.*--)(?!-?[0-9])[\w-]+(-[\w-]+|[a-zA-Z])?$')


class HTMLRuntimeMixin(HTMLIterator):
    def __init__(self, args: list[Chunk | Thunk]):
        self.args = args
        self.marker = HTML

    def convert(self, obj: Any, conv: Conversion) -> str:
        match conv:
            case 'a':
                return ascii(obj)
            case 'r':
                return repr(obj)
            case 's' | None:
                return str(obj)

    def unpack_value(self, value, fspec) -> Iterable[HTML]:
        match value:
            case HTML():
                yield value
            case str():
                yield HTML(escape(format(value, fspec)))
            case Iterable():
                for elem in value:
                    yield from self.unpack_value(elem, fspec)
            case _:
                yield HTML(escape(format(value, fspec)))

    def getvalue(self, index: int) -> Iterable[HTML]:
        # FIXME handle conversions with conv
        arg = self.args[index]
        value = arg.getvalue()
        fspec = '' if arg.formatspec is None else arg.formatspec
        yield from self.unpack_value(value, fspec)

    def check_valid_tagname(self, tagname: str):
        if not tagname_re.match(tagname):
            raise ValueError(f'Invalid tag name: {tagname!r}')

    def check_valid_attribute_name(self, attribute_name: str):
        if not attribute_name_re.match(attribute_name):
            raise ValueError(f'Invalid attribute name: {attribute_name!r}')

    def get_tagname(self, *builder: str) -> str:
        tagname = ''.join(builder)
        self.check_valid_tagname(tagname)
        return HTML(f"<{tagname}")

    def get_end_tagname(self, *builder: str) -> str:
        tagname = ''.join(builder)
        self.check_valid_tagname(tagname)
        return HTML(f"</{tagname}>")

    def get_key_value(self, k_builder: list[str], v: bool | dict | list[Any]) -> str:
        k = ''.join(k_builder)
        self.check_valid_attribute_name(k)
        match k, v:
            # Only show boolean keys if True
            case _, True:
                return HTML(str(k))
            case _, False:
                return None
            # FIXME are there other HTML attributes that use this formatting?
            # Also we may want to support this formatting with the
            # formatspec, such as for custom elements
            case 'style', dict() as d:
                styling_list = []
                for sub_k, sub_v in d.items():
                    styling_list.append(f'{sub_k}: {sub_v}')
                styling = escape('; '.join(styling_list), quote=True)
                return HTML(f'{k}="{styling}"')
            case _, list() as v_list:
                quoted_v = escape(''.join(str(part) for part in v_list), quote=True)
                return HTML(f'{k}="{quoted_v}"')
            case _, _:
                quoted_v = escape(str(v), quote=True)
                return HTML(f'{k}="{quoted_v}"')


    def get_attrs_dict(self, value: Any):
        attrs = []
        match value:
            case dict() as d:
                for k, v in d.items():
                    setting = self.get_key_value([k], v)
                    if setting is not None:
                        attrs.append(setting)
                return HTML(' '.join(attrs))
            case _:
                raise ValueError(f'Attributes must be a dict, not {type(value)!r}')


class HTMLCompiler(BaseCompiler):
    # Optimized for WSGI consumption, so returns a generator, in a
    # code-generated __iter__ method.

    # Given that functionality could also capture a lot of information
    # on any interpolations, so as to simplify that, let's make it a
    # subclass on a passed-in class, constructing with type.

    # NOTE it should be straightforward to construct from this example
    # such variants as one that supports ASGI or is eager and returns a
    # single block of text.

    def __init__(self, indent=2):
        self.yield_block = []
        self.preamble = \
            f"""
def __iter__(self):
"""
        super().__init__()
        self.name = '__iter__'

    def __call__(self, tag: Tag) -> Callable:
        code = super().__call__(tag)
        return type('TemplateRenderer', (HTMLRuntimeMixin,), {'__iter__': code})

    def add_yield_string(self, s: str):
        # NOTE enables coalescing static lines of text together in one
        # yield
        self.yield_block.append(s)

    def add_interpolation(self, i: Interpolation) -> str:
        local_var = f'_arg{i.index}'
        formatspec = '' if i.formatspec is None else i.formatspec
        if i.conv is None:
            self.add_line(
                f'{local_var} = format(self.args[{i.index}].getvalue(), {formatspec!r})')
        else:
            self.add_line(
                f'{local_var} = format(self.convert(self.args[{i.index}].getvalue(), {i.conv!r}), {formatspec!r})')
        return local_var

    def add_child_interpolation(self, i: Interpolation) -> str:
        formatspec = '' if i.formatspec is None else i.formatspec
        self.add_line(f'yield from self.getvalue({i.index})')

    def add_line(self, line: str):
        if self.yield_block:
            block = ''.join(self.yield_block)
            self.lines.append(f"    yield self.marker('''{block}''')")
            self.yield_block = []
        self.lines.append(f'    {line}')

    def get_name_builder(self, elements: E):
        name_args = []
        for item in elements:
            match item:
                case str() as s:
                    name_args.append(repr(s))
                case Interpolation() as i:
                    name_args.append(self.add_interpolation(i))
        return ', '.join(name_args)

    def compile(self, tag: Tag, level=1):
        tagname = None

        # process the starting tagname itself
        match tag:
            case Tag(tagname=[str() as tagname]):
                # no interpolations, so can special case
                self.add_yield_string(f'<{tagname}')
            case Tag():
                tagname_builder = self.get_name_builder(tag.tagname)
                self.add_line(f'yield self.get_tagname({tagname_builder})')

        for k, v in tag.attrs:
            match k:
                case [str()]:
                    match v:
                        case [str()]:
                            self.add_yield_string(f' {k[0]}="{v[0]}"')
                        case None:
                            # eg 'disabled'
                            self.add_yield_string(f' {k[0]}')
                        case _:
                            self.add_yield_string(f' ')
                            self.add_line(f'yield self.get_key_value({k[0]!r}, [{self.get_name_builder(v)}])')
                case [Interpolation() as i] if v is None:
                    self.add_yield_string(' ')
                    name_arg = self.add_interpolation(i)
                    self.add_line(f'yield self.get_attrs_dict({name_arg})')
                case _:
                    match v:
                        case None:
                            raise ValueError('Cannot resolve multiple interpolations into a dict/bool interpolation')
                        case _:
                            self.add_yield_string(' ')
                            self.add_line(f'yield self.get_key_value([{self.get_name_builder(k)}], [{self.get_name_builder(v)}])')

        # close the start tag
        self.add_yield_string('>')

        # process children
        for child in tag.children:
            match child:
                case str():
                    self.add_yield_string(escape(child))
                case Interpolation() as i:
                    self.add_child_interpolation(i)
                case Tag() as t:
                    self.compile(t, level + 1)

        # end the tag
        if tagname is None:
            self.add_line(f'yield self.get_end_tagname({tagname_builder})')
        else:
            self.add_yield_string(f'</{tagname}>')

        # ensure all blocks are closed out
        if level == 1:
            self.add_line('')
