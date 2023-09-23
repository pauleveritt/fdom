"""Test an example."""
import pytest

from . import main


@pytest.mark.skip("Bug: Inner loop does not interpolate.")
def test_main() -> None:
    """Ensure the demo matches expected."""
    assert main() == '<ul title="Hello"><li>World</li><li>Universe</li></ul>'
