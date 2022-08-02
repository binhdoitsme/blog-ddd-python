import os

from hashids import Hashids


class IdMapper:
    def __init__(self) -> None:
        self._hasher = Hashids(os.environ.get("SECRET"), min_length=16)

    def encode(self, id: int) -> str:
        return self._hasher.encode(id)

    def decode(self, id: str) -> int:
        return int(self._hasher.decode(id))
