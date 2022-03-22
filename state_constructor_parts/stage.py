from __future__ import annotations

import logging
from typing import List, AnyStr, Optional

from global_transferable_entities.scope import Scope
from global_transferable_entities.user import User
from state_constructor_parts.action import Action
from state_constructor_parts.filter import InputFilter
from message_parts.message import Message
from typing_module_extensions.choice import Choice


class Stage:

    def __init__(self,
                 name: AnyStr,
                 message: Optional[Message | Choice[Message]] = None,
                 user_input_actions: Optional[List[Action] | Choice[List[Action]]] = None,
                 user_input_filter: Optional[InputFilter | Choice[InputFilter]] = None):
        self._name = name
        self._message = message
        self._user_input_actions = user_input_actions
        self._user_input_filter = user_input_filter
        logging.info("Stage with name {} created".format(self._name))

    def get_name(self) -> AnyStr:
        return self._name

    def get_message(self,
                    scope: Scope,
                    user: User) -> Optional[Message]:
        if isinstance(self._message, Choice):
            return self._message.get(scope, user)
        elif isinstance(self._message, Message):
            return self._message

    def get_user_input_actions(self,
                               scope: Scope,
                               user: User) -> Optional[List[Action]]:
        if isinstance(self._user_input_actions, Choice):
            return self._user_input_actions.get(scope, user)
        elif isinstance(self._user_input_actions, List):
            return self._user_input_actions
        return None

    def get_user_input_filter(self,
                              scope: Scope,
                              user: User) -> Optional[InputFilter]:
        if isinstance(self._user_input_filter, Choice):
            return self._user_input_filter.get(scope, user)
        elif isinstance(self._user_input_filter, InputFilter):
            return self._user_input_filter

    def is_allowed_input(self,
                         input_string: AnyStr,
                         scope: Scope,
                         user: User) -> bool:
        if self._user_input_filter is not None:
            if not self._user_input_filter.is_allowed_input(input_string):
                return False

        if message := self.get_message(scope, user):
            if keyboard := message.get_keyboard(scope, user):
                if not keyboard.is_non_keyboard_input_allowed:
                    keyboard_buttons_strings = \
                        [button.get_text(scope, user) for button in keyboard.get_buttons(scope, user)]
                    if input_string not in keyboard_buttons_strings:
                        return False
        return True

    def process_input(self,
                      input_string: AnyStr,
                      scope: Scope,
                      user: User) -> Message:
        if user_input_actions := self.get_user_input_actions(scope, user):
            for user_input_action in user_input_actions:
                user_input_action.apply(scope, user, input_string)
        try:
            keyboard_buttons = self.get_message(scope, user).get_keyboard(scope, user).get_buttons(scope, user)
            for keyboard_button in keyboard_buttons:
                if input_string == keyboard_button.get_text(scope, user):
                    for button_action in keyboard_button.get_actions():
                        button_action.apply(scope, user, input_string)
        except AttributeError:
            pass

        transition_user_stage = scope.get_stage(user.get_current_stage_name())
        return transition_user_stage.get_message(scope, user)
