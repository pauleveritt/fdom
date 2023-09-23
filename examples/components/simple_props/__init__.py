"""Use ``children`` as a built-in "prop"."""
from fdom.htmltag import html


def Heading(title):
    """Default heading."""
    return html"<h1>{title}</h1>"


def main() -> str:
    """Main entry point."""
    return html'<{Heading} title="My Title" />'


if __name__ == '__main__':
    print(main())
