"""Show the component in the VDOM."""
from fdom.htmltag import html


def Heading():
    """The default heading."""
    return html"<h1>My Title</h1>"


def main():
    """Main entry point."""
    return html"<{Heading} />"


if __name__ == '__main__':
    print(main())
