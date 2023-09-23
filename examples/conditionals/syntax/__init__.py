"""Use normal Python syntax for conditional rendering in a template."""
from fdom.htmltag import html


def main() -> str:
    """Main entry point."""
    message = "Say Howdy"
    not_message = "So Sad"
    show_message = True
    return html"""
      <div>
        <h1>Show?</h1>
        {message if show_message else not_message}
      </div>  
    """


if __name__ == '__main__':
    print(main())
