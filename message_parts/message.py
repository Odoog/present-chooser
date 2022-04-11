from __future__ import annotations

import sys
from typing import List, AnyStr, Optional, Callable, Union

from telegram.parsemode import ParseMode

from typing_module_extensions.choice import Choice

from os.path import exists

import hashlib

import requests

class MessageText:

    def __init__(self,
                 text: AnyStr | Callable[..., AnyStr],
                 parse_mode: ParseMode = ParseMode.HTML):
        self.text = text() if callable(text) else text
        self.parse_mode = parse_mode


class MessagePicture:
    def __init__(self,
                 picture_file_disk_source: Optional[AnyStr] = None,
                 picture_file_telegram_id: Optional[AnyStr] = None,
                 picture_file_link: Optional[AnyStr] = None):
        if picture_file_disk_source is None and picture_file_telegram_id is None and picture_file_link is None:
            raise ValueError('File disk source and file telegram id and photo link cannot both be none')
        self.picture_file_disk_source = picture_file_disk_source
        self.picture_file_telegram_id = picture_file_telegram_id
        self.picture_file_link = picture_file_link

    def get_picture_source(self):
        if self.picture_file_link is not None: # Телеграм плохо работает (работает ли вообще?) с web link на image, поэтому закачиваем изображение к себе
            link_hash = hashlib.md5(str.encode(self.picture_file_link)).hexdigest()
            file_disc_source = 'resources/temp_image{0}.jpg'.format(link_hash)
            if not exists(file_disc_source):
                img_data = requests.get(self.picture_file_link).content
                with open(file_disc_source, 'wb') as handler:
                    handler.write(img_data)
            return file_disc_source
        return self.picture_file_disk_source or self.picture_file_telegram_id


class MessageKeyboardButton:
    def __init__(self,
                 text: AnyStr | Choice[AnyStr] | Callable[..., AnyStr] | Callable[..., Choice[AnyStr]],
                 actions: 'Optional[List[Action]]' = None):
        self._text = text
        self._actions = actions

    def get_text(self,
                 scope: 'Scope',
                 user: 'User') -> AnyStr:
        if isinstance(self._text, Choice):
            message_text = self._text.get(scope, user)
            return message_text(scope, user) if callable(message_text) else message_text
        else:
            return self._text(scope, user) if callable(self._text) else self._text

    def get_actions(self, scope, user) -> 'List[Action]':
        actions = self._actions(scope, user) if callable(self._actions) else self._actions
        actions = actions.get(scope, user) if isinstance(actions, Choice) else actions
        actions = [] if actions is None else actions
        actions = [action(scope, user) if callable(action) else action for action in actions]
        return actions


class MessageKeyboard:

    def __init__(self,
                 buttons: Union[
                     List[MessageKeyboardButton | Callable[..., MessageKeyboardButton]],
                     Choice[List[MessageKeyboardButton | Callable[..., MessageKeyboardButton]]],
                     Callable[..., List[MessageKeyboardButton | Callable[..., MessageKeyboardButton]]],
                     Callable[..., Choice[List[MessageKeyboardButton | Callable[..., MessageKeyboardButton]]]]
                 ],
                 buttons_layout: Optional[List[int]] = None,
                 is_non_keyboard_input_allowed: bool = False,
                 is_inline_keyboard: bool = False):
        self._buttons = buttons
        self._buttons_layout = buttons_layout or [sys.maxsize]
        self.is_non_keyboard_input_allowed = is_non_keyboard_input_allowed
        self.is_inline_keyboard = is_inline_keyboard

    def get_buttons(self,
                    scope: 'Scope',
                    user: 'User',
                    keyboard_type: AnyStr = "reply") -> List[List[MessageKeyboardButton]]:
        buttons = self._buttons(scope, user) if callable(self._buttons) else self._buttons
        buttons = buttons.get(scope, user) if isinstance(buttons, Choice) else buttons
        buttons = [button(scope, user) if callable(button) else button for button in buttons]
        buttons_layout = []
        current_button_index = 0
        current_layout_row_index = 0
        while current_button_index < len(buttons) and current_layout_row_index < len(self._buttons_layout):
            count_of_buttons_to_add = min(len(buttons) - current_button_index, self._buttons_layout[current_layout_row_index])
            buttons_layout.append(buttons[current_button_index : current_button_index + count_of_buttons_to_add])
            current_layout_row_index += 1
            current_button_index += count_of_buttons_to_add
        return buttons_layout


class Message:

    def __init__(self,
                 text: Optional[
                    Union[
                         MessageText | Choice[MessageText],
                         Callable[..., MessageText] | Choice[Callable[..., MessageText]]
                    ]
                 ] = None,
                 picture: Optional[
                    Union[
                         MessagePicture | Choice[MessagePicture],
                         Callable[..., MessagePicture] | Choice[Callable[..., MessagePicture]]
                    ]
                 ] = None,
                 keyboard: Optional[MessageKeyboard | Choice[MessageKeyboard]] = None,
                 should_replace_last_message: bool = False,
                 should_delete_last_message: bool = False):
        self._text = text
        self._picture = picture
        self._keyboard = keyboard
        self.should_replace_last_message = should_replace_last_message
        self.should_delete_last_message = should_delete_last_message

    def get_text(self,
                 scope: 'Scope',
                 user: 'User') -> Optional[MessageText]:
        if isinstance(self._text, Choice):
            text = self._text.get(scope, user)
            return text(scope, user) if callable(text) else text
        else:
            return self._text(scope, user) if callable(self._text) else self._text

    def get_picture(self,
                    scope: 'Scope',
                    user: 'User') -> Optional[MessagePicture]:
        if isinstance(self._picture, Choice):
            picture = self._picture.get(scope, user)
            return picture(scope, user) if callable(picture) else picture
        else:
            return self._picture(scope, user) if callable(self._picture) else self._picture

    def get_keyboard(self,
                     scope: 'Scope',
                     user: 'User') -> Optional[MessageKeyboard]:
        if isinstance(self._keyboard, Choice):
            return self._keyboard.get(scope, user)
        else:
            return self._keyboard


class SimpleTextMessage(Message):
    def __init__(self,
                 text: AnyStr):
        super().__init__(text=MessageText(text))
