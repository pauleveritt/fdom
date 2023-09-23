"""Pass a component as a prop value."""
from fdom.htmltag import html


def DefaultHeading():
    """The default heading."""
    return html"<h1>Default Heading</h1>"


def Body(heading):
    """The body which renders the heading."""
    return html"<body><{heading} /></body>"


def main() -> str:
    """Main entry point."""
    return html"<{Body} heading={DefaultHeading} />"


if __name__ == '__main__':
    print(main())
