"""Get a variable from a passed-in ``prop``."""
from fdom.htmltag import html


def Hello(name):
    """A simple hello component."""
    return html"<div>Hello {name}</div>"


def main():
    """Main entry point."""
    return Hello(name="viewdom")


if __name__ == '__main__':
    print(main())
