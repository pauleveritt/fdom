"""Test an example."""
import pytest

from . import main


@pytest.mark.skip("Bug: Triple-quoted strings do not parse")
def test_main() -> None:
    """Ensure the demo matches expected."""
    assert main() == "<h1>Show?</h1>Say Howdy"
