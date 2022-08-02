import dataclasses
from typing import Any, Callable, List, Set, TypeVar

T = TypeVar("T")


def own_properties(cls: type) -> Set[str]:
    return {
        key
        for key, value in cls.__dict__.items()
        if isinstance(value, property)
    }


def fields(cls: type) -> Set[str]:
    return {field.name for field in dataclasses.fields(cls)}


def properties(cls: type) -> Set[str]:
    props: List[str] = []
    for kls in cls.mro():
        props += own_properties(kls)

    return set(props)


def with_kwargs(callable: Callable[..., T]):
    def call(kwargs: dict[str, Any]):
        return callable(**kwargs)

    return call
