"""Simple example of inserting a variable value into a template."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    name = "viewdom"
    result = html"<div>Hello {name}</div>"
    return result


if __name__ == '__main__':
    print(main())
