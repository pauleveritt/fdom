"""Call a function from inside a template expression."""
from fdom.htmltag import html

def make_bigly(name: str) -> str:
    """A function returning a string, rather than a component."""
    return f"BIGLY: {name.upper()}"


def main() -> str:
    """Main entry point."""
    name = "fdom"
    return html"<div>Hello {make_bigly(name)}</div>"


if __name__ == '__main__':
    print(main())