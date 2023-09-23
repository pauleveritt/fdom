"""Subcomponents."""
from fdom.htmltag import html

title = "My Todos"


def Todo(label):
    """An individual to do component."""
    return html"<li>{label}</li>"


def TodoList(todos):
    """A to do list component."""
    return html"<ul>{[Todo(label) for label in todos]}</ul>"


def main() -> str:
    """Main entry point."""
    todos = ["first"]
    return html"""
      <h1>{title}</h1>
      <{TodoList} todos={todos} />
    """


if __name__ == '__main__':
    print(main())
