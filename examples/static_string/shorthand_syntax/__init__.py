"""Shorthand syntax for attribute values means no need for double quotes."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    result = html'<div class={"Container1".lower()}>Hello World</div>'
    return result


if __name__ == '__main__':
    print(main())
