import logging
import traceback
from functools import wraps
from typing import Callable, Type, TypeVar, Union

T = TypeVar("T")
AnyException = TypeVar("AnyException", bound=Exception)
Source = TypeVar("Source", bound=Exception)
Target = Union[Type[AnyException], Callable[[], AnyException]]


def mask(from_: Type[Source], to_: Target):
    def inner(callable: Callable[..., T]):
        @wraps(callable)
        def handle_inner(*args, **kwargs):
            try:
                return callable(*args, **kwargs)
            except from_ as e:
                logging.error(e)
                traceback.print_exc()
                raise to_(e)

        return handle_inner

    return inner
