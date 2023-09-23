"""Generate a list of VDOMs then use in a render."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    message = "Hello"
    names = ["World", "Universe"]
    items = [html"<li>{label}</li>" for label in names]
    return html'<ul title="{message}">{items}</ul>'



if __name__ == '__main__':
    print(main())
