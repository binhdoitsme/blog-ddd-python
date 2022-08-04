from datetime import datetime
from functools import partial
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import BIGINT, INT, TIMESTAMP, Column, String, asc, desc
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session

from domain.blog import Blog, BlogId, BlogRepository
from domain.exceptions import RepositoryError
from domain.user import User, UserId, UserRepository
from utilities.db import LazySequence
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
    timestamp = Column(
        "timestamp", TIMESTAMP, primary_key=True, default=datetime.utcnow()
    )

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


class SQLABlogRepository(BlogRepository):
    default_orderings = [
        desc(BlogHistoryRecord.blog_id),
        asc(BlogHistoryRecord.timestamp),
    ]

    def __init__(self, session: Session) -> None:
        self.session = session
        self._page = None
        self._page_size = None

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
    
    def to_paging(self, slice: slice):
        start_index, stop_index = slice.start, slice.stop
        page_size = stop_index - start_index
        def apply_paging(query: sqlalchemy.orm.Query):
            return query.limit(page_size).offset(start_index)
        return apply_paging
    
    def get_sliced_result(self, slice: slice, query: sqlalchemy.orm.Query):
        records = self.to_paging(slice)(query).all()
        return self.to_domain(records)

    @mask(from_=SQLAlchemyError, to_=RepositoryError)
    def find(self) -> Sequence[Blog]:
        query = self.session.query(BlogHistoryRecord)
        query = query.order_by(*self.default_orderings)
        return LazySequence(populator=partial(self.get_sliced_result, query=query))

    def find_by(self, **matcher: Dict[str, Any]) -> Sequence[Blog]:
        assert set(matcher.keys()).issubset(properties(Blog))
        query = self.session.query(BlogHistoryRecord).filter_by(**matcher)
        query = query.order_by(*self.default_orderings)
        return LazySequence(populator=self.get_sliced_result)


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
