import abc
from dataclasses import dataclass
from typing import Optional

from utilities.domain import Id


class UserId(Id[int]):
    counter = 0

    @classmethod
    def next_value(cls) -> int:
        cls.counter += 1
        return cls.counter


@dataclass
class User:
    id: UserId
    username: str

class UserRepository(abc.ABC):
    """Raise RepositoryError if any problem occurs."""
    @abc.abstractmethod
    def find_by_id(self, id: UserId) -> Optional[User]:
        ...
