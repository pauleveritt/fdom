"""Test an example."""
import pytest

from . import main


@pytest.mark.skip("Bug: Triple-quoted string do not parse.")
def test_main() -> None:
    """Ensure the demo matches expected."""
    result = main()
    assert "<li>1</li>" in result
