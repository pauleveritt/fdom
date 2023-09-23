"""Loop through values in a template and render them."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    message = "Hello"
    names = ["World", "Universe"]
    return html'<ul title="{message}">{[html('<li>{name}</li>')for name in names]}</ul>'


if __name__ == '__main__':
    print(main())
