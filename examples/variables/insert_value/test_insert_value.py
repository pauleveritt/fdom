"""Simple variable insertion."""
from . import main


def test_main() -> None:
    """Ensure the demo matches expected."""
    assert main() == "<div>Hello viewdom</div>"
