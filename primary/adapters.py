from datetime import datetime
from typing import Generic, Optional, TypeVar
from fastapi import HTTPException

from fastapi_class.routable import Routable
from fastapi_class.decorators import get
from pydantic import BaseModel

from application import BlogDto, BlogService
from domain.exceptions import RepositoryError
from utilities.exceptions import mask
from utilities.mappers import IdMapper

T = TypeVar("T")


class CommonModel(BaseModel, Generic[T]):
    success: bool
    data: list[T]


class SimpleUserModel(BaseModel):
    id: str
    username: str


class BlogResponseModel(BaseModel):
    id: str
    title: str
    content: str
    created_at: datetime
    created_by: SimpleUserModel
    history: Optional[list[dict[str, str]]]


class BlogListResponse(CommonModel[BlogResponseModel]):
    next_page: Optional[int]


class BlogRouter(Routable):
    def __init__(self, blog_service: BlogService, id_mapper: IdMapper) -> None:
        super().__init__()
        self.blog_service = blog_service
        self.id_mapper = id_mapper

    def convert_dto(self, instance: BlogDto) -> BlogResponseModel:
        history = (
            None
            if instance.history is None
            else list(map(dict, instance.history))
        )
        return BlogResponseModel(
            id=self.id_mapper.encode(instance.id),
            title=instance.title,
            content=instance.content,
            created_at=instance.created_at,
            created_by=SimpleUserModel(
                id=self.id_mapper.encode(instance.user.id),
                username=instance.user.username,
            ),
            history=history,
        )

    @get("", response_model=BlogListResponse, response_model_exclude_none=True)
    @mask(
        from_=RepositoryError,
        to_=lambda _: HTTPException(
            500, "Error in database operations, please check server logs."
        ),
    )
    def read_blogs(self, page: int = 1, limit: int = 10):
        blog_service = self.blog_service
        current_page = blog_service.get_blogs(page=page, page_size=limit)
        has_next_page = True
        if len(current_page) < limit:
            has_next_page = False
        if has_next_page:
            next_page = blog_service.get_blogs(page=page + 1, page_size=limit)
            if len(next_page) == 0:
                has_next_page = False
        return BlogListResponse(
            success=True,
            data=list(map(self.convert_dto, current_page)),
            next_page=page + 1 if has_next_page else None,
        )
