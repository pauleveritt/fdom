from dataclasses import dataclass
from fdom.htmltag import html


class Upper:
    def __ror__(self, value) -> str:
        return (str(value)).upper()

    __call__ = __ror__

upper = Upper()


@dataclass(frozen=True)
class User:
    name: str
    title: str


def test_pipe():
    user = User(name='Arthur', title='King')
    assert html'<h1>Report for {user.title} {user.name | upper}</h1>' == \
        '<h1>Report for King ARTHUR</h1>'
