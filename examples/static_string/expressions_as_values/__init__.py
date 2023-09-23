"""Use a simple Python expression as the attribute value."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    result = html'<div class="container{1}">Hello World</div>'
    return result


if __name__ == '__main__':
    print(main())
