"""Render a triple-quoted strings."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    return html"""
            <ul>
              <li>1</li>
              <li>2</li>
              <li>3</li>
            </ul>
            """


if __name__ == '__main__':
    print(main())
