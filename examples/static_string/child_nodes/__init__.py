"""Child nodes become part of the VDOM."""
from fdom.astparser import as_ast, Tag


def main() -> Tag:
    """Main entry point."""
    vdom = as_ast"<div>Hello <span>World<em>!</em></span></div>"
    return vdom


if __name__ == '__main__':
    print(main())
