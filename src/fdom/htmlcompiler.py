from collections.abc import Generator
from html import escape

from fdom.astparser import Interpolation, Tag
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
        return f'<{"".join(builder)}>'

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

    def __init__(self, indent=2):
        self.yield_block = []
        self.preamble = \
            f"""
class CompiledHMTL(HTMLGeneratorMixin):
  def __iter__(self):
    _args = self.args
    _get_tagname = self.get_tagname_from_builder
    _escape = self.html_escape
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
            block = '\n'.join(self.yield_block)
            self.lines.append(f'    yield """{block}"""')
            self.yield_block = []
        self.lines.append(f'    {line}')

    def compile(self, tag: Tag, level=1):
        tagname = None

        # process the tagname itself
        match tag:
            case Tag(tagname=[str() as tagname]):
                # no interpolations, so can special case
                self.add_yield_string(f'<{tagname}>')
            case Tag():
                tag_args = []
                for item in tag.tagname:
                    match item:
                        case str() as s:
                            tag_args.append(repr(s))
                        case Interpolation() as i:
                            tag_args.append(self.add_interpolation(i))
                    tagname_builder = ', '.join(tag_args)
                self.add_line(f'yield _get_tagname({tagname_builder})')

        # process children
        for child in tag.children:
            match child:
                case str():
                    self.add_yield_string(escape(child))
                case Interpolation() as i:
                    self.add_line(level, f'yield _escape({self.add_interpolation(i)})')
                case Tag() as t:
                    self.compile(t, level + 1)

        if tagname is None:
            self.add_line(f'yield _get_end_tagname({tagname_builder})')
        else:
            self.add_yield_string(f'</{tagname}>')
        # ensure all blocks are closed out -
        # FIXME this needs another arg for the root level to maximize coalescing
        if level == 1:
            self.add_line('')
