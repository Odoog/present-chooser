import logging
from typing import Callable, TypeVar, Dict, Any, Generic, TYPE_CHECKING, Type

T = TypeVar('T')


class InstanceOrCallable(Generic[T]):
    def __init__(self,
                 instance: 'Callable[[Scope, User], T] | T'):
        self._instance = instance

    def get(self,
            scope: 'Scope',
            user: 'User') -> T:
        return self._instance(scope, user) if callable(self._instance) else self._instance
