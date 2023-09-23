"""Getting a doctype into the rendered output is a bit tricky."""
from markupsafe import Markup

from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    doctype = Markup("<!DOCTYPE html>\n")
    result = html"{doctype}<div>Hello World</div>"
    return result


if __name__ == '__main__':
    print(main())
