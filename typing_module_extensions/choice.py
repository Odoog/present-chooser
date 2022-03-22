import logging
from typing import Callable, TypeVar, Dict, Any, Generic, TYPE_CHECKING

OptionalOutputClass = TypeVar('OptionalOutputClass')
ConditionOutputClass = TypeVar('ConditionOutputClass')


class Choice(Generic[OptionalOutputClass]):
    def __init__(self,
                 function: 'Callable[[Scope, User], ConditionOutputClass]',
                 outputs: Dict[ConditionOutputClass, OptionalOutputClass]):
        self.function = function
        self.outputs = outputs

    def get(self,
            scope: 'Scope',
            user: 'User') -> OptionalOutputClass:
        function_output = self.function(scope, user)
        if function_output not in self.outputs:
            logging.error("Optional object with this function output is not specified")
        else:
            return self.outputs[function_output]
