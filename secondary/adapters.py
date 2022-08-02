from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import BIGINT, INT, TIMESTAMP, Column, String, asc, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session

from domain.blog import Blog, BlogId, BlogRepository
from domain.exceptions import RepositoryError
from domain.user import User, UserId, UserRepository
from utilities.db import SupportsPaging
from utilities.exceptions import mask
from utilities.strings import ne, wraps_name
from utilities.typings import properties


@as_declarative()
class Base(object):
    @declared_attr
    def __tablename__(cls):
        tokens = wraps_name(cls.__name__).tokenize()
        tokens = list(filter(ne("record"), tokens))
        return "_".join(tokens)


class BlogHistoryRecord(Base):
    blog_id = Column("blog_id", BIGINT, primary_key=True)
    title = Column("title", String(127))
    content = Column("content", String(1024))
    created_by = Column("created_by", INT)
    timestamp = Column("timestamp", TIMESTAMP, primary_key=True, default=datetime.utcnow())

    def __init__(
        self, /, blog_id: int, title: str, content: str, created_by: int
    ) -> None:
        self.blog_id = blog_id
        self.title = title
        self.content = content
        self.created_by = created_by

    def dict_without_id(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "timestamp": self.timestamp,
            "created_by": self.created_by,
        }


class SQLABlogRepository(BlogRepository, SupportsPaging):
    default_orderings = [
        desc(BlogHistoryRecord.blog_id),
        asc(BlogHistoryRecord.timestamp),
    ]

    def __init__(self, session: Session) -> None:
        self.session = session
        self._page = None
        self._page_size = None

    def page(self, page=1) -> SupportsPaging:
        self._page = page
        return self

    def page_size(self, size=25) -> SupportsPaging:
        self._page_size = size
        return self

    def save(self, blog: Blog) -> None:
        record = BlogHistoryRecord(
            blog_id=blog.id.value,
            title=blog.title,
            content=blog.content,
            created_by=blog.created_by.value,
        )
        self.session.add(record)
        self.session.commit()

    def remove(self, blog: Blog):
        filterer = BlogHistoryRecord.blog_id == blog.id.value
        blog_history_items = self.session.query(BlogHistoryRecord)
        blog_history_items.filter(filterer).delete(synchronize_session=False)
        self.session.commit()

    def to_domain(self, blog_history: List[BlogHistoryRecord]) -> List[Blog]:
        if len(blog_history) == 0:
            return []
        blogs: Dict[int, List[Dict[str, Any]]] = dict()
        for blog_history_entry in blog_history:
            blog_id = blog_history_entry.blog_id
            if blog_id not in blogs:
                blogs[blog_id] = list()
            blogs[blog_id].append(blog_history_entry.dict_without_id())
        results: List[Blog] = []
        for blog_id, history in blogs.items():
            latest_state = history[-1]
            blog = Blog(
                id=BlogId(blog_id),
                title=latest_state["title"],
                content=latest_state["content"],
                author_id=UserId(history[0]["created_by"]),
                history=history,
            )
            results.append(blog)
        return results

    @mask(from_=SQLAlchemyError, to_=RepositoryError)
    def find(self) -> Iterable[Blog]:
        blog_history_query = self.session.query(BlogHistoryRecord)
        blog_history_query = blog_history_query.order_by(*self.default_orderings)
        if self._page and self._page_size:
            limit = self._page_size
            offset = self._page_size * (self._page - 1)
            blog_history_query = blog_history_query.limit(limit).offset(offset)
        return self.to_domain(blog_history_query.all())

    def find_by(self, **matcher: Dict[str, Any]) -> Iterable[Blog]:
        assert set(matcher.keys()).issubset(properties(Blog))
        query = self.session.query(BlogHistoryRecord).filter_by(**matcher)
        blog_history = query.order_by(*self.default_orderings).all()
        return self.to_domain(blog_history)


class UserRecord(Base):
    id = Column("id", INT, primary_key=True)
    username = Column("username", String(127), unique=True)


class SQLAUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def to_domain(self, record: UserRecord):
        return User(id=UserId(record.id), username=record.username)

    def find_by_id(self, id: UserId) -> Optional[User]:
        record = self.session.query(UserRecord).filter_by(id=id.value).first()
        if record is None:
            return None
        return self.to_domain(record)
