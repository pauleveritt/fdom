from collections.abc import Generator

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
        self.preamble = \
            f"""
class CompiledHMTL(HTMLGeneratorMixin):
  def __iter__(self):
    _args = self.args
    _get_tagname = self.get_tagname_from_builder
"""
        super().__init__()

    def compile(self, tag: Tag, level=1):
        tagname = None
        match tag:
            case Tag(tagname=[str() as tagname]):
                # no interpolations, so can special case
                self.add_line(level, f"yield '<{tagname}>'")
            case Tag():
                tag_args = []
                for item in tag.tagname:
                    match item:
                        case str() as s:
                            tag_args.append(repr(s))
                        case Interpolation() as i:
                            self.add_line(level, f'_arg{i.index} = format(_args[{i.index}].getvalue(), {i.formatspec})')
                            tag_args.append(f'_arg{i.index}')
                    tagname_builder = ', '.join(tag_args)
                self.add_line(level, f'yield _get_tagname({tagname_builder})')

        if tagname is None:
            self.add_line(level, f'yield _get_end_tagname({tagname_builder})')
        else:
            self.add_line(level, f"yield '</{tagname}>'")
