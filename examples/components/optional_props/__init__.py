"""Optional props."""
from fdom.htmltag import html


def Heading(title="My Title"):
    """The default heading."""
    return html"<h1>{title}</h1>"


def main() -> str:
    """Main entry point."""
    return html"<{Heading} />"


if __name__ == '__main__':
    print(main())
