from __future__ import annotations

import abc
from abc import abstractclassmethod
from typing import Generic, Optional, TypedDict, TypeVar

T = TypeVar("T")


class Id(abc.ABC, Generic[T]):
    _value: T

    @abstractclassmethod
    def next_value(cls) -> T:
        ...

    def __init__(self, value: Optional[T] = None):
        self._value = value if value is not None else self.next_value()
    
    @property
    def value(self) -> T:
        return self._value

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self._value})"


class Entity(Generic[T]):
    pass


class Root(Entity[T], Generic[T]):
    pass
