from typing import Protocol


class SupportStr(Protocol):

    def __str__(self) -> str: ...
