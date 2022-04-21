from __future__ import annotations

import itertools
import logging
from typing import List, AnyStr, Optional

from global_transferable_entities.scope import Scope
from global_transferable_entities.user import User
from state_constructor_parts.action import Action
from state_constructor_parts.filter import InputFilter
from message_parts.message import Message, SimpleTextMessage, MessageText
from state_constructor_parts.stats import Stats
from typing_module_extensions.choice import Choice


class Stage:

    def __init__(self,
                 name: AnyStr,
                 message: Optional[Message | Choice[Message]] = None,
                 prerequisite_actions: Optional[List[Action]] = None,
                 user_input_actions: Optional[List[Action] | Choice[List[Action]]] = None,
                 user_input_filter: Optional[InputFilter | Choice[InputFilter]] = None,
                 statistics: Optional[List[Stats]] = None,
                 is_gatehouse: bool = False): # TODO: Автоматическое определение IsGatehouse в зависимости от прикрепленных actions.
        self._name = name
        self._message = message
        self._prerequisite_actions = prerequisite_actions
        self._user_input_actions = user_input_actions
        self._user_input_filter = user_input_filter
        self._statistics = statistics
        self._is_gatehouse = is_gatehouse

        logging.info("Stage with name {} created".format(self._name))

    def is_gatehouse(self) -> bool:
        return self._is_gatehouse

    def get_name(self) -> AnyStr:
        return self._name

    def get_message(self,
                    scope: Scope,
                    user: User) -> Optional[Message]:
        if isinstance(self._message, Choice):
            return self._message.get(scope, user)
        elif isinstance(self._message, Message):
            return self._message

    def get_prerequisite_actions(self,
                                 scope: Scope,
                                 user: User) -> List[Action]:
        return self._prerequisite_actions or []

    def get_user_input_actions(self,
                               scope: Scope,
                               user: User) -> Optional[List[Action]]:
        if isinstance(self._user_input_actions, Choice):
            return self._user_input_actions.get(scope, user)
        elif isinstance(self._user_input_actions, List):
            return self._user_input_actions
        return None

    def get_statistics(self,
                       scope: Scope,
                       user: User) -> Optional[List[Stats]]:
        return self._statistics

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
                        [button.get_text(scope, user) for button in list(itertools.chain(*keyboard.get_buttons(scope, user)))]
                    if input_string not in keyboard_buttons_strings:
                        return False
        return True

    def count_statistics(self,
                         input_string: AnyStr,
                         scope: Scope,
                         user: User,
                         stage: Stage):
        if statistics := self.get_statistics(scope, user):
            for statistic in statistics:
                statistic.step(scope, user, stage, input_string)

    def process_input(self,
                      input_string: AnyStr,
                      scope: Scope,
                      user: User) -> Message:

        if not self.is_allowed_input(input_string, scope, user):
            transition_user_stage = scope.get_stage(user.get_current_stage_name())
            transition_user_message = transition_user_stage.get_message(scope, user)
            transition_user_message.set_onetime_text_processor_method(lambda text: MessageText("Выберите один из вариантов и нажмите.\n\n" + text.text))
            return transition_user_message

        prerequisite_actions = self.get_prerequisite_actions(scope, user)
        for prerequisite_action in prerequisite_actions:
            prerequisite_action.apply(scope, user, input_string)

        if user_input_actions := self.get_user_input_actions(scope, user):
            for user_input_action in user_input_actions:
                user_input_action.apply(scope, user, input_string)

        try:
            keyboard_buttons = list(itertools.chain(*self.get_message(scope, user).get_keyboard(scope, user).get_buttons(scope, user)))
            for keyboard_button in keyboard_buttons:
                if input_string == keyboard_button.get_text(scope, user):
                    for action in keyboard_button.get_actions(scope, user):
                        if action is not None:
                            action.apply(scope, user, input_string)
        except AttributeError:
            pass

        transition_user_stage = scope.get_stage(user.get_current_stage_name())
        return transition_user_stage.get_message(scope, user)
