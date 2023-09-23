"""Generators as components."""
from fdom.htmltag import html


def Todos():
    """A sequence of li items."""
    for todo in ["First", "Second"]:
        yield html"<li>{todo}</li>"


def main() -> str:
    """Main entry point."""
    return html"<ul><{Todos}/></ul>"


if __name__ == '__main__':
    print(main())
