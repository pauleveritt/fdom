"""Test an example."""
from . import main
from fdom.astparser import Tag


def test_main() -> None:
    """Ensure the demo matches expected."""
    expected = Tag(
        tagname=["div"],
        attrs=[(['class'], ['container'])],
        children=["Hello World"],
    )
    actual = main()
    # Let's look at each individually
    assert actual.tagname == expected.tagname
    assert actual.attrs == expected.attrs
    assert actual.children == expected.children
