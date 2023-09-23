"""Prop values from scope variables."""
from fdom.htmltag import html


def Heading(title):
    """The default heading."""
    return html"<h1>{title}</h1>"


this_title = "My Title"


def main() -> str:
    """Main entry point."""
    return html"<{Heading} title={this_title} />"


if __name__ == '__main__':
    print(main())
