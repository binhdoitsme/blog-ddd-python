from __future__ import annotations

from typing import Generic, Protocol, TypeVar


class SupportsPaging(Protocol):
    def page(self, page=1) -> SupportsPaging:
        ...

    def page_size(self, size=25) -> SupportsPaging:
        ...


T = TypeVar("T", bound=SupportsPaging)


class Paged(Generic[T]):
    def __init__(self, pager: T) -> None:
        self.pager = pager

    def by(self, page=1, size=25):
        if page < 1:
            page = 1
        if size < 25:
            size = 25
        return self.pager.page(page).page_size(size)
