"""Boolean attribute values are reduced during rendering."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    result = html"<div editable={True}>Hello World</div>"
    return result


if __name__ == '__main__':
    print(main())
