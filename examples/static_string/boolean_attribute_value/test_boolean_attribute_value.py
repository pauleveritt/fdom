"""Test an example."""
import pytest

from . import main


@pytest.mark.skip("Feature: Does not collapse boolean")
def test_main() -> None:
    """Ensure the demo matches expected."""
    assert main() == "<div editable>Hello World</div>"
