from __future__ import annotations
from typing import Callable, AnyStr, Optional, TYPE_CHECKING, Any


# Определяет действие, активация которого происходит во время обработки пользовательского ответа
# на определённом этапе. Из-за этого у такого действия есть строке ввода пользователя.
from telegram import Message


class Action:

    def __init__(self,
                 action_function: 'Callable[[Scope, User, Optional[AnyStr]], ...]'):
        self._action_function = action_function

    def apply(self,
              scope: 'Scope',
              user: 'User',
              input_string: Optional[AnyStr] = None):
        self._action_function(scope, user, input_string)


# Определяет действие, активация которого происходит в момент посылки пользователю сообщения.
# Из-за этого у такого действия есть доступ к посланному Message в момент применения.
class PrerequisiteAction:

    def __init__(self,
                 action_function: 'Callable[[Scope, User, Optional[Message]], ...]'):
        self._action_function = action_function

    def apply(self,
              scope: 'Scope',
              user: 'User',
              sent_message: Optional[Message] = None):
        self._action_function(scope, user, sent_message)


class ActionBack(Action):
    def __init__(self):
        super().__init__(lambda scope, user, input_string: user.change_stage(user.stages_history[-2]))


class ActionBackToMainStage(Action):
    def __init__(self):
        super().__init__(lambda scope, user, input_string: user.change_stage(scope.main_stage))


class ActionChangeStage(Action):
    def __init__(self,
                 stage_name: AnyStr):
        super().__init__(lambda scope, user, input_string: user.change_stage(stage_name))


class ActionChangeUserVariable(Action):
    def __init__(self,
                 variable_name: AnyStr,
                 variable_value: Any):
        if callable(variable_value):
            super().__init__(lambda scope, user, input_string: user.set_variable(variable_name, variable_value(scope, user)))
        else:
            super().__init__(lambda scope, user, input_string: user.set_variable(variable_name, variable_value))


class ActionChangeUserVariableToInput(Action):
    def __init__(self,
                 variable_name: AnyStr):
        super().__init__(lambda scope, user, input_string: user.set_variable(variable_name, input_string))


class ActionChangeGlobalVariable(Action):
    def __init__(self,
                 variable_name: AnyStr,
                 variable_value: AnyStr):
        super().__init__(lambda scope, user: scope.set_variable(variable_name, variable_value))


class ActionGetInput(Action):
    def __init__(self):
        super().__init__(lambda scope, user, input_string: input_string)
