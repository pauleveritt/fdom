"""Overriding a default "built-in" component."""
from fdom.htmltag import html


def DefaultHeading():  # pragma: nocover
    """The default heading."""
    return html"<h1>Default Heading</h1>"


def OtherHeading():
    """Another heading used in another condition."""
    return html"<h1>Other Heading</h1>"


def Body(heading=DefaultHeading):
    """Render the body with a heading based on which is passed in."""
    return html"<body><{heading} /></body>"


def main() -> str:
    """Main entry point."""
    return html"<{Body} heading={OtherHeading}/>"


if __name__ == '__main__':
    print(main())
