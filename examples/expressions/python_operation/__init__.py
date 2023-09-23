"""Python operation in the expression."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    name = "viewdom"
    result = html"<div>Hello {name.upper()}</div>"
    return result


if __name__ == '__main__':
    print(main())
