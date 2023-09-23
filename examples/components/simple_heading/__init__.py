"""Simple function component, nothing dynamic, that returns a VDOM."""
from fdom.htmltag import html


def Heading():
    """The default heading."""
    return html"<h1>My Title</h1>"


def main() -> str:
    """Main entry point."""
    return html"<{Heading} />"


if __name__ == '__main__':
    print(main())
