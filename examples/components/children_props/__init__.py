"""Children as props."""
from fdom.htmltag import html


def Heading(children, title):
    """The default heading."""
    return html"<h1>{title}</h1><div>{children}</div>"


def main() -> str:
    """Main entry point."""
    return html'<{Heading} title="My Title">Child</{Heading}>'


if __name__ == '__main__':
    print(main())
