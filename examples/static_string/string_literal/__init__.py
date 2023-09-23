"""Render just a string literal."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    result = html"Hello World"
    return result


if __name__ == '__main__':
    print(main())
