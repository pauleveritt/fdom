"""Get a variable from an import."""

from examples.variables.value_from_import.constants import name
from fdom.htmltag import html


# TODO: What's the correct return type here?
def Hello():
    """A simple hello component."""
    return html"<div>Hello {name}</div>"


# TODO: What's the correct return type here?
def main():
    """Main entry point."""
    return Hello()


if __name__ == '__main__':
    print(main())
