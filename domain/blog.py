import abc
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from domain.user import UserId
from utilities.domain import Id
from utilities.typings import fields


@dataclass
class BlogHistory:
    title: str
    content: str
    timestamp: datetime = datetime.utcnow()

    def asdict(self) -> Dict[str, Any]:
        return self.__dict__

    @classmethod
    def from_dict(cls, props: Dict[str, Any]):
        assert fields(cls).issubset(set(props.keys()))
        return BlogHistory(**{k: v for k, v in props.items() if k in fields(cls)})


class BlogId(Id[int]):
    counter = 0

    @classmethod
    def next_value(cls):
        cls.counter += 1
        return cls.counter


class BlogProperties:
    __MAX_TITLE_LENGTH__ = 127
    __MAX_CONTENT_LENGTH__ = 1024

    title: str
    content: str

    @classmethod
    def assert_title(cls, title: Optional[str]) -> None:
        if title is None:
            return
        assert len(title) <= cls.__MAX_TITLE_LENGTH__

    @classmethod
    def assert_content(cls, content: Optional[str]) -> None:
        if content is None:
            return
        assert len(content) <= cls.__MAX_CONTENT_LENGTH__

    def __init__(
        self, *, title: Optional[str] = None, content: Optional[str] = None
    ) -> None:
        self.assert_title(title)
        self.assert_content(content)
        if title:
            self.title = title
        if content:
            self.content = content

    def asdict(self) -> Dict[str, Any]:
        return self.__dict__

    def __str__(self) -> str:
        return self.__dict__.__str__()


class Blog:
    _id: BlogId
    _props: BlogProperties
    _history: List[BlogHistory]

    def __init__(
        self,
        title: str,
        content: str,
        author_id: UserId,
        id: BlogId = BlogId(),
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        props = BlogProperties(title=title, content=content)
        self._id = id
        self._props = props
        self._author_id = author_id
        self._history = (
            list(map(BlogHistory.from_dict, history))
            if history is not None
            else [BlogHistory(props.title, props.content)]
        )

    @property
    def id(self) -> BlogId:
        return self._id

    @property
    def history(self) -> List[Dict[str, Any]]:
        return list(map(BlogHistory.asdict, self._history))

    @property
    def title(self) -> str:
        return self._props.title

    @property
    def content(self) -> str:
        return self._props.content

    @property
    def created_by(self) -> UserId:
        return self._author_id

    @property
    def created_at(self) -> datetime:
        return next(iter(self._history)).timestamp

    def update(self, properties: BlogProperties) -> None:
        if self._props == properties:
            return
        history_entry = BlogHistory(properties.title, properties.content)
        self._props = properties
        self._history.append(history_entry)

    def __str__(self) -> str:
        return f"Blog(id={self._id}, props={self._props}, history={self.history})"


class BlogRepository(abc.ABC):
    """Raise RepositoryError if any problem occurs."""

    @abc.abstractmethod
    def save(self, blog: Blog) -> None:
        ...

    @abc.abstractmethod
    def remove(self, blog: Blog) -> None:
        ...

    @abc.abstractmethod
    def find(self) -> Iterable[Blog]:
        ...

    @abc.abstractmethod
    def find_by(self, **matcher: Dict[str, Any]) -> Iterable[Blog]:
        ...
