from tagstr import Thunk

from fdom.compiler import make_key, ASTParser, escape_placeholder, unescape_placeholder, vdom, BaseCompiler


def test_make_key_single_string():
    result = make_key("Hello")
    assert result == ("Hello",)


def test_make_key_single_thunk():
    raw = "raw"
    conv = "c"
    formatspec = "f"
    thunk = Thunk(getvalue=lambda x: x, raw=raw, conv=conv, formatspec=formatspec)
    result = make_key(thunk)
    assert result[0][0] is None
    assert result[0][1] is None
    assert result[0][2] is conv
    assert result[0][3] is formatspec


def test_ast_parser_construction():
    ast = ASTParser()
    assert ast.root.tagname is None
    assert ast.root.attrs == {}
    assert ast.root.children == []
    assert ast.stack == [ast.root]
    assert list(ast.interpolations) == []


def test_escape_placeholder_none():
    result = escape_placeholder("nada")
    assert result == "nada"


def test_escape_placeholder_one():
    result = escape_placeholder("hello $world")
    assert result == "hello $$world"


def test_unescape_placeholder_none():
    result = unescape_placeholder("nada")
    assert result == "nada"


def test_unescape_placeholder_one():
    result = unescape_placeholder("hello $$world")
    assert result == "hello $world"


def test_make_key_multiple_strings():
    result = make_key("Hello", "World")
    assert result == ("Hello", "World")


def test_vdom_all():
    tag_name = "div"
    attributes = {"id": "d1"}
    children = ["Hello"]
    this_vdom = vdom(tag_name, attributes, children)
    assert this_vdom == {"tagName": tag_name, "attributes": attributes, "children": children}


def test_base_compiler_construction():
    bc = BaseCompiler()
    assert bc.indent == 2
    assert bc.name == "compiled"


def test_base_compiler_add_line():
    bc = BaseCompiler()
    bc.lines = []  # TODO Remove this later
    bc.add_line(1, "hello")
    assert bc.lines == ["    hello"]
    bc.add_line(1, "world")
    assert bc.code == "    hello\n    world"
