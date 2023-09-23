"""Test an example."""
import pytest

from . import main


@pytest.mark.skip("Bug: Fails when no wrapping tag")
def test_main() -> None:
    """Ensure the demo matches expected."""
    assert main() == "<!DOCTYPE html>\n<div>Hello World</div>"
