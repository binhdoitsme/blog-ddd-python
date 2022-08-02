import abc
from re import finditer
from typing import Iterable


class MemberName(abc.ABC):
    def __init__(self, value: str) -> None:
        self.value = value

    @abc.abstractmethod
    def tokenize(self) -> Iterable[str]:
        ...


class CamelCasedName(MemberName):
    match_regex = r".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)"

    def tokenize(self) -> Iterable[str]:
        matches = finditer(self.match_regex, self.value)
        return [m.group(0).lower() for m in matches]


class SnakeCasedName(MemberName):
    def tokenize(self) -> Iterable[str]:
        return self.value.lower().split("_")


def wraps_name(value: str) -> MemberName:
    if "_" in value:
        return SnakeCasedName(value)
    return CamelCasedName(value)


def ne(value: str):
    def handle(other: str):
        return other != value

    return handle
