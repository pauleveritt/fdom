from collections.abc import Generator
from html import escape

from fdom.astparser import E, Interpolation, Tag, is_static_element
from fdom.basecompiler import BaseCompiler
from fdom.thunky import Chunk, Thunk


class HTML:
    """Marker class for HTML content"""
    pass


class HTMLGeneratorMixin(HTML):
    def __init__(self, *args):
        self.args = args
        # initialize other state

    def html_escape(self, s):
        match s:
            case HTML():
                return s
            case str():
                return escape(s)

    def get_tagname_from_builder(self, builder):
        # FIXME need to sanitize input here
        return f'<{"".join(builder)}'

    def get_attrs(self, *args):
        pass

    # need to consider formatting
    # for tags, data, honor the formatspec - but check if a valid tag
    # for attributes, guess with respect to placement - style, boolean tags like disabled
    # yield as soon as possible

    # def get_data(self, *args):
    #     for arg in args:
    #         match arg:
    #             case Chunk() as s:
    #                 yield s.decoded.encode('utf-8')
    #             case Thunk() as t:
    #                 value = t.getvalue()
    #                 match value:
    #                     case HTML():
    #                         yield from value
    #                     case Generator():
    #                         for v in value:
    #                             yield self.escape(v)


    #                 if isinstance(value, Generator):
    #                     yield


class HTMLCompiler(BaseCompiler):
    # Optimized for WSGI consumption, so returns a generator, in a codegenerated
    # __iter__ method.

    # Given that functionality could also capture a lot of information on any
    # interpolations, so as to simplify that, let's make it a subclass on a
    # passed-in class, constructing with type.

    # It should be straightforward to construct an ASGI variant, or conversely
    # one that is eager and returns a single block of text.

    # FIXME use type() constructor instead of hardcoding with respect to a name
    # (HTMLGeneratorMixin)

    def __init__(self, indent=2):
        self.yield_block = []
        self.preamble = \
            f"""
class CompiledHTML(HTMLGeneratorMixin):
  def __iter__(self):
    _args = self.args
    _get_tagname = self.get_tagname_from_builder
    _get_attrs_dict = self.get_attrs_dict
    _get_key_value = self.get_key_value
    _escape = self.html_escape

    # FIXME add missing runtime methods, plus additional localization
"""
        super().__init__()

    def add_yield_string(self, s: str):
        # enables coalescing static lines of text together in one yield
        self.yield_block.append(s)

    def add_interpolation(self, i: Interpolation) -> str:
        local_var = f'_arg{i.index}'
        self.add_line(f'{local_var} = format(_args[{i.index}].getvalue(), {i.formatspec})')
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
                self.add_line(f'yield _get_tagname({tagname_builder})')

        attrs = {}
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
                    self.add_line(f'yield _get_attrs_dict({i.index})')
                case _:
                    match v:
                        case None:
                            raise ValueError('Cannot resolve multiple interpolations into a dict/bool interpolation')
                        case _:
                            self.add_yield_string(' ')
                            self.add_line(f'yield _get_key_value([{self.get_name_builder(k)}], [{self.get_name_builder(v)}])')

        # close the start tag
        self.add_yield_string('>\n')

        # process children
        for child in tag.children:
            match child:
                case str():
                    self.add_yield_string(escape(child))
                case Interpolation() as i:
                    # NOTE there is a subtle distinction here between
                    # - compile time: html.escape
                    # - run time: _escape, which takes in account the HTML marker
                    self.add_line(level, f'yield _escape({self.add_interpolation(i)})')
                case Tag() as t:
                    self.compile(t, level + 1)

        # end the tag
        if tagname is None:
            self.add_line(f'yield _get_end_tagname({tagname_builder})')
        else:
            self.add_yield_string(f'</{tagname}>\n')

        # ensure all blocks are closed out
        if level == 1:
            self.add_line('')
