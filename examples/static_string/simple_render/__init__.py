"""Render a string wrapped by a div."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    result = html"<div>Hello World</div>"
    return result

if __name__ == '__main__':
    print(main())
