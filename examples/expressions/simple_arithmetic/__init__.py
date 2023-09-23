"""Simple arithmetic expression in a template."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    return html"<div>Hello {1 + 3}</div>"


if __name__ == '__main__':
    print(main())
