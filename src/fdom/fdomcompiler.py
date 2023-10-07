from abc import abstractmethod
from collections.abc import Generator, Iterable
from html import escape
from typing import Any, Callable
import re

from fdom.astparser import E, Interpolation, Tag, is_static_element
from fdom.basecompiler import BaseCompiler
from fdom.taglib import Chunk, Conversion, Thunk


"""
What do we want here?

<html attr=attr1>...</html>

self.tag.html(attrs={...}, children=[])
plus be able to support interpolations

<{MyComponent}>...</...>

just assumes MyComponent will resolve to a valid reference;
this can also be arbitrary, with any desired initialization/setup

<h{level}>...</...>
resolves to self.tag.h{level}


Generated code:
I don't see how we can avoid a standard functional evaluation order
here, but the rendering of the DOM nodes itself can presumably do
diffing/patching, etc
"""


class HTML(str):
    """Marker class for HTML content"""
    pass


attribute_name_re = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_\-\.]*$')
tagname_re = re.compile(r'^(?!.*--)(?!-?[0-9])[\w-]+(-[\w-]+|[a-zA-Z])?$')


class FdomRuntimeMixin:
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


class FdomCompiler(BaseCompiler):

    def __init__(self, indent=2, name='__call__', mixin=FdomRuntimeMixin):
        self.mixin = mixin
        self.preamble = f"""
def {name}(self):
  return \\"""
        super().__init__(indent=indent, name=name)

    def __call__(self, tag: Tag) -> Callable:
        code = super().__call__(tag)
        return type('TemplateRenderer', (self.mixin,), {self.name: code})

    def get_name_builder(self, elements: E):
        name_args = []
        for item in elements:
            match item:
                case str() as s:
                    name_args.append(repr(s))
                case Interpolation() as i:
                    name_args.append(f'self.getvalue({i.index})')
        return ', '.join(name_args)

    def compile(self, tag: Tag, level=1):
        # process the starting tagname itself
        match tag:
            case Tag(tagname=[str() as tagname]):
                self.add_line(level, f'self.tags.{tagname}(')
            case Tag(tagname=[Interpolation() as i]):
                self.add_line(level, f'self.args[{i.index}].getvalue()(')
            case Tag():
                tagname_builder = self.get_name_builder(tag.tagname)
                self.add_line(level, f'self.dynamic_tag([{tagname_builder}])(')

        self.add_line(level + 1, 'attrs={')
        for k, v in tag.attrs:
            match k:
                case [str()]:
                    match v:
                        case [str()]:
                            self.add_line(level + 2, f'{k[0]!r}: {v[0]!r},')
                        case None:
                            self.add_line(level + 2, f'{k[0]!r}: True,')
                case [Interpolation() as i] if v is None:
                    self.add_line(level + 2, f'**self.get_attrs_dict({i.index}),')
                case _:
                    match v:
                        case None:
                            raise ValueError('Cannot resolve multiple interpolations into a dict/bool interpolation')
                        case _:
                            self.add_line(f'yield self.get_key_value([{self.get_name_builder(k)}], [{self.get_name_builder(v)}])')
        self.add_line(level + 1, '}, ')

        # process children
        self.add_line(level + 1, 'children=[')
        for child in tag.children:
            match child:
                case str():
                    self.add_line(level + 2, f'{child!r},')
                case Interpolation() as i:
                    self.add_line(level + 2, f'self.getvalue({i.index}),')
                case Tag() as t:
                    self.compile(t, level + 2)
        self.add_line(level + 1, ']')

        # end the tag
        self.add_line(level, ')')
