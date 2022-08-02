from datetime import datetime
from functools import partial
from typing import Any, Dict, Iterable, List, NamedTuple, Optional

from domain.blog import Blog, BlogRepository
from domain.user import User, UserId, UserRepository
from utilities.db import Paged
from utilities.typings import with_kwargs


class BlogHistoryDto(NamedTuple):
    timestamp: datetime
    title: str
    content: str


class UserDto(NamedTuple):
    id: int
    username: str


class BlogDto(NamedTuple):
    id: int
    title: str
    content: str
    created_at: datetime
    user: UserDto
    history: Optional[list[BlogHistoryDto]] = None


class BlogDtoAssembler:
    def to_dto(self, blog: Blog, user: User, with_history=False) -> BlogDto:
        kwargs: dict[str, Any] = {
            "id": blog.id.value,
            "title": blog.title,
            "content": blog.content,
            "created_at": blog.created_at,
        }
        if user is not None:
            kwargs["user"] = UserDto(id=user.id.value, username=user.username)
        if with_history:
            kwargs["history"] = [*map(with_kwargs(BlogHistoryDto), blog.history)]

        return BlogDto(**kwargs)


class BlogService:
    def __init__(
        self, blog_repository: BlogRepository, user_repository: UserRepository
    ) -> None:
        self.blog_repository = blog_repository
        self.user_repository = user_repository
        self.dto_assembler = BlogDtoAssembler()

    def create_blog(self, title: str, content: str, created_by: int) -> BlogDto:
        user_id = UserId(created_by)
        user = self.user_repository.find_by_id(user_id)
        blog = Blog(title, content, UserId(created_by))
        return self.dto_assembler.to_dto(blog, user)

    def get_blogs(self, page=1, page_size=25) -> Iterable[BlogDto]:
        repo: BlogRepository = Paged(self.blog_repository).by(page, page_size)
        blogs = repo.find()
        blogs_by_user: Dict[UserId, List[Blog]] = dict()
        for blog in blogs:
            user_id = blog.created_by
            if user_id not in blogs_by_user:
                blogs_by_user[user_id] = []
            blogs_by_user[user_id].append(blog)
        results: List[BlogDto] = []
        for user_id, blogs in blogs_by_user.items():
            user = self.user_repository.find_by_id(user_id)
            to_dto = partial(self.dto_assembler.to_dto, user=user)
            results.extend(list(map(to_dto, blogs)))
        return results

    def get_blog_by_id(self, blog_id: int) -> Optional[BlogDto]:
        search_result = self.blog_repository.find_by(created_by=UserId(blog_id))
        blog: Blog = next(iter(search_result))
        user = self.user_repository.find_by_id(blog.created_by)
        return self.dto_assembler.to_dto(blog, user, with_history=True)
