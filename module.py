import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from application import BlogService
from primary.adapters import BlogRouter
from secondary.adapters import SQLABlogRepository, SQLAUserRepository
from utilities.mappers import IdMapper


class Module:
    def __init__(self) -> None:
        engine = create_engine(os.environ.get("DB_CONNECTION_STR"))
        db_session: Session = sessionmaker(bind=engine)()
        blog_repository = SQLABlogRepository(db_session)
        user_repository = SQLAUserRepository(db_session)
        blog_service = BlogService(blog_repository, user_repository)
        id_mapper = IdMapper()
        blog_router = BlogRouter(blog_service, id_mapper)
        self.app = FastAPI()
        self.app.include_router(blog_router.router, prefix="/blogs")

    def run(self):
        uvicorn.run(self.app, debug=True)
