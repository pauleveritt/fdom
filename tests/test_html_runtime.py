from fdom.htmlcompiler import HTMLRuntimeMixin
from fdom.taglib import Thunk


def test_convert():
    mixin = HTMLRuntimeMixin([])
    assert mixin.convert('foo', 'a') == "'foo'"
    assert mixin.convert('foo', 'r') == "'foo'"
    assert mixin.convert('foo', 's') == 'foo'


def test_recursive_escape():
    class HelloWorldHTMLGenerator(HTMLRuntimeMixin):
        def __iter__(self):
            yield '<body>'
            yield '<div>Hello, world</div>'
            yield '</body>'

    inner = HelloWorldHTMLGenerator([])
    outer = HTMLRuntimeMixin([])
    assert list(outer.recursive_escape(inner)) == [
            '<body>',
            '<div>Hello, world</div>',
            '</body>'
    ]


def test_get_tagname_no_interpolations():
    mixin = HTMLRuntimeMixin([])
    assert mixin.get_tagname('a', 'b', 'c') == '<abc'


def test_get_tagname_with_interpolations():
    class TagNameGenerator(HTMLRuntimeMixin):
        def __iter__(self):
            a = self.args[0].getvalue()
            b = self.args[1].getvalue()
            yield self.get_tagname(a, 'X', b)

    gen = TagNameGenerator([
        Thunk(lambda: 'foo', '"foo"', None, None),
        Thunk(lambda: 'bar', '"bar"', None, None),
    ])
    assert list(gen) == ['<fooXbar']


# FIXME add some more attribute examples here, such as boolean attributes
def test_get_key_value():
    class AttrGenerator(HTMLRuntimeMixin):
        def __iter__(self):
            k = self.args[0].getvalue()
            v = self.args[1].getvalue()
            yield self.get_key_value(k, v)

    gen = AttrGenerator([
        Thunk(lambda: 'style', '"style"', None, None),
        Thunk(lambda: {'margin': '15px', 'line-height': 1.5, 'text-align': 'center'}, '...', None, None),
    ])
    assert list(gen) == ['style="margin: 15px; line-height: 1.5; text-align: center"']


def test_get_attrs_dict():
    class AttrGenerator(HTMLRuntimeMixin):
        def __iter__(self):
            d = self.args[0].getvalue()
            yield self.get_attrs_dict(d)

    gen = AttrGenerator([
        Thunk(lambda: {'foo': 42, 'blink': 'on', 'disabled': False}, '...', None, None),
    ])
    assert list(gen) == ['foo="42" blink="on"']
