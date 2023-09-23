"""Test an example."""
import pytest

from . import main


@pytest.mark.skip("Bug: fails when no tag")
def test_main() -> None:
    """Ensure the demo matches expected."""
    assert main() == "Hello World"

