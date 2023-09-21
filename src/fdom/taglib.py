from typing import Any, Callable, Literal, NamedTuple, Protocol, Self


class Chunk(str):
    def __new__(cls, value: str) -> Self:
        chunk = super().__new__(cls, value)
        chunk._decoded = None
        return chunk

    @property
    def decoded(self) -> str:
        """Convert string to bytes then, applying decoding escapes.

        Uses the same internal code functionality as Python's parser
        does to perform the actual decode.
        """
        if self._decoded is None:
            self._decoded = self.encode('utf-8').decode('unicode-escape')
        return self._decoded


Conversion = Literal['a', 'r', 's'] | None


class Thunk(NamedTuple):
    getvalue: Callable[[], Any]
    text: str
    conv: Conversion = None
    formatspec: str | None = None


def convert_to_proposed_scheme(*args: str|tuple):
    proposed_args = []
    for arg in args:
       match arg:
            case Chunk() | Thunk():
                # ignore previous conversions for simplicity
                proposed_args.append(arg)
            case str():
               proposed_args.append(Chunk(arg))
            case _, _, _, _:
               proposed_args.append(Thunk(*arg))
    return tuple(proposed_args)


class Tag(Protocol):
    def __call__(self, *args: Chunk | Thunk) -> Any:
        ...


if __name__ == '__main__':
    def mytag(*args):
        return convert_to_proposed_scheme(*args)

    trade = 'shrubberies'
    mytag'Did you say "{trade}"?'
