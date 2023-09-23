"""The prop has a default value, so caller doesn't have to provide it."""
from fdom.htmltag import html


def Hello(name="viewdom"):
    """A simple hello component."""
    return html"<div>Hello {name}</div>"


def main() -> str:
    """Main entry point."""
    return Hello()


if __name__ == '__main__':
    print(main())
