"""Test an example."""
from fdom.astparser import Tag
from . import main


def test_main() -> None:
    """Ensure the demo matches expected."""
    assert main() == Tag(
        tagname=["div"],
        attrs=[],
        children=[
            "Hello ",
            Tag(
                tagname=["span"],
                attrs=[],
                children=["World", Tag(tagname=["em"], attrs=[], children=["!"])],
            ),
        ],
    )
