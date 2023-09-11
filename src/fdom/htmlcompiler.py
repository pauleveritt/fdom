from abc import abstractmethod
from collections.abc import Generator
from html import escape
from typing import Any, Callable

from fdom.astparser import E, Interpolation, Tag, is_static_element
from fdom.basecompiler import BaseCompiler
from fdom.taglib import Chunk, Conversion, Thunk


class HTML:
    """Marker class for HTML content"""
    @abstractmethod
    def __iter__(self):
        ...


class HTMLRuntimeMixin(HTML):
    def __init__(self, args: list[Chunk | Thunk]):
        self.args = args
        self.marker_class = HTML

    def convert(self, obj: Any, conv: Conversion) -> str:
        match conv:
            case 'a':
                return ascii(obj)
            case 'r':
                return repr(obj)
            case 's' | None:
                return str(obj)

    # NOTE there is a subtle distinction here between
    # - compile time: html.escape
    # - run time: recursive_escape, which takes in account the HTML
    #   marker

    def recursive_escape(self, s: str | HTML):
        match s:
            case HTML():
                yield from s
            case str():
                return escape(s)
            case _:
                raise ValueError(f'Expected a string or HTML, not {type(s)}')

    def get_tagname(self, *builder):
        # FIXME raise ValueError if a dynamic tagname results in an
        # invalid name, but first determine what are invalid tagnames
        # from an appropriate RFC

        # NOTE the quoting here - builder can be made up of
        # single-quoted strings (because of the use of repr) or variable
        # names
        return f"<{''.join(builder)}"

    def get_end_tagname(self, *builder: str):
        # FIXME ditto
        return f"</{''.join(builder)}>"

    def get_key_value(self, k: str, v: Any) -> str:
        # FIXME need to consider invalid keys
        match k, v:
            # Only show boolean keys if True
            case _, True:
                return str(k)
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
                return f'{k}="{styling}"'
            case _, _:
                quoted_v = escape(str(v), quote=True)
                return f'{k}="{quoted_v}"'

    def get_attrs_dict(self, value: Any):
        attrs = []
        match value:
            case dict() as d:
                for k, v in d.items():
                    setting = self.get_key_value(k, v)
                    if setting is not None:
                        attrs.append(setting)
                return ' '.join(attrs)
            case _:
                raise ValueError('Attributes must be a dict')


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

    def add_line(self, line: str):
        if self.yield_block:
            block = ''.join(self.yield_block)
            self.lines.append(f'    yield """{block}"""')
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

        # FIXME what escaping/sanity checking is required? For now, be simplistic
        for k, v in tag.attrs:
            match k:
                case [str()]:
                    match v:
                        case [str()]:
                            self.add_yield_string(f' {k[0]}="{v[0]}"')
                        case None:
                            # eg 'disabled'
                            self.add_yield_string(f' {k[0]}')
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
        self.add_yield_string('>\n')

        # process children
        for child in tag.children:
            match child:
                case str():
                    self.add_yield_string(escape(child))
                case Interpolation() as i:
                    self.add_line(f'yield self.recursive_escape({self.add_interpolation(i)})')
                case Tag() as t:
                    self.compile(t, level + 1)

        # end the tag
        if tagname is None:
            self.add_line(f'yield self.get_end_tagname({tagname_builder})')
        else:
            self.add_yield_string(f'</{tagname}>\n')

        # ensure all blocks are closed out
        if level == 1:
            self.add_line('')
