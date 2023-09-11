from fdom.taglib import Thunk

from fdom.astparser import (
    as_ast,
    make_key,
    escape_placeholder,
    unescape_placeholder,
    ASTParser,
    Interpolation,
    Tag,
    )


def test_parse_no_interpolations():
    template = as_ast'<input readonly placeholder="Favorite color">Blue</input>'
    assert template == \
        Tag(tagname=['input'],
            attrs=[(['readonly'], None), (['placeholder'], ['Favorite color'])],
            children=['Blue'])


def test_parse_typical_interpolations():
    template = as_ast'<div style={style}>some {text}</div>'
    assert template == \
        Tag(tagname=['div'],
            attrs=[(['style'], [Interpolation(index=1, conv=None, formatspec=None)])],
            children=['some ', Interpolation(index=3, conv=None, formatspec=None)])


def test_parse_tagname_interpolation():
    template = as_ast'<h{level}>Heading</h{level}>'
    assert template == \
        Tag(tagname=['h', Interpolation(index=1, conv=None, formatspec=None)],
            attrs=[],
            children=['Heading'])


def test_parse_tagname_more_interpolation():
    template = as_ast'<h{level}>Heading at {level}: some {text}</h{level}>'
    assert template == \
        Tag(tagname=['h', Interpolation(index=1, conv=None, formatspec=None)],
            attrs=[],
            children=[
                'Heading at ',
                Interpolation(index=3, conv=None, formatspec=None),
                ': some ',
                Interpolation(index=5, conv=None, formatspec=None)])


def test_parse_complex_tagname():
    template = as_ast'<{x}{y}{z}bar>foo</{x}{y}{z}bar>'
    assert template == \
        Tag(
            tagname=[
                Interpolation(index=1, conv=None, formatspec=None),
                Interpolation(index=2, conv=None, formatspec=None),
                Interpolation(index=3, conv=None, formatspec=None),
                'bar'
            ],
            attrs=[],
            children=['foo'])


def test_parse_complex_tagname_only_interpolations():
    template = as_ast'<{x}{y}{z}>foo</{x}{y}{z}>'
    assert template == \
        Tag(
            tagname=[
                Interpolation(index=1, conv=None, formatspec=None),
                Interpolation(index=2, conv=None, formatspec=None),
                Interpolation(index=3, conv=None, formatspec=None),
            ],
            attrs=[],
            children=['foo'])


def test_make_key_single_string():
    result = make_key("Hello")
    assert result == ("Hello",)


def test_make_key_single_thunk():
    conv = 's'
    formatspec = 'some-format'
    thunk = Thunk(
        getvalue=lambda: some_expr,
        text='some_expr',
        conv=conv,
        formatspec=formatspec)
    result = make_key(thunk)[0]
    assert result.conv == conv
    assert result.formatspec == formatspec


def test_ast_parser_construction():
    ast = ASTParser()
    assert ast.root.tagname is None
    assert ast.root.attrs == []
    assert ast.root.children == []
    assert ast.stack == [ast.root]
    assert list(ast.interpolations) == []


def test_escape_placeholder_none():
    result = escape_placeholder('nada')
    assert result == 'nada'


def test_escape_placeholder_one():
    result = escape_placeholder('hello $world')
    assert result == 'hello $$world'


def test_unescape_placeholder_none():
    result = unescape_placeholder('nada')
    assert result == 'nada'


def test_unescape_placeholder_one():
    result = unescape_placeholder('hello $$world')
    assert result == 'hello $world'


def test_make_key_multiple_strings():
    result = make_key('Hello', 'World')
    assert result == ('Hello', 'World')
