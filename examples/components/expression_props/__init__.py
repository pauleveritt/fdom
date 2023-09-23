"""Pass a Python symbol as part of an expression."""
from fdom.htmltag import html


def Heading(title):
    """The default heading."""
    return html"<h1>{title}</h1>"


def main() -> str:
    """Main entry point."""
    return html'<{Heading} title={"My Title"} />'


if __name__ == '__main__':
    print(main())
