"""Show the VDOM itself."""
from fdom.astparser import as_ast, Tag


def main() -> Tag:
    """Main entry point."""
    result = as_ast'<div class="container">Hello World</div>'
    return result


if __name__ == '__main__':
    print(main())
