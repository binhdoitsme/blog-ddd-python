from __future__ import annotations

from io import UnsupportedOperation
from typing import Callable, Protocol, Sequence, TypeVar, Union

T = TypeVar("T")
PaginatedQuery = TypeVar(
    "PaginatedQuery", bound="SupportsPaginatedQuery", covariant=True
)


class SupportsPaginatedQuery(Protocol[PaginatedQuery]):
    def limit(self, limit: int) -> PaginatedQuery:
        ...

    def offset(self, offset: int) -> PaginatedQuery:
        ...


class SupportsPaging:
    def to_paging(self, slice: slice):
        start_index, stop_index = int(slice.start), int(slice.stop)
        page_size = stop_index - start_index

        def apply_paging(
            query: SupportsPaginatedQuery[PaginatedQuery],
        ) -> PaginatedQuery:
            return query.limit(page_size).offset(start_index)

        return apply_paging


class LazySequence(Sequence[T]):
    def __init__(
        self,
        populator: Callable[[slice], Sequence[T]],
    ) -> None:
        super().__init__()
        self._container: Sequence[T] = list()
        self.ready = False
        self.populate = populator

    def populate_if_not_ready(self, key: slice):
        if not self.ready:
            self._container = self.populate(key)
            self.ready = True

    def __getitem__(self, key: Union[int, slice]):
        if isinstance(key, int):
            raise UnsupportedOperation()
        self.populate_if_not_ready(key)
        return self._container

    def __len__(self) -> int:
        return len(self._container)
