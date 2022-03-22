from __future__ import annotations
from typing import List, AnyStr, Optional, Callable, Union

from telegram.parsemode import ParseMode

from typing_module_extensions.choice import Choice


class MessageText:

    def __init__(self,
                 text: AnyStr | Callable[..., AnyStr],
                 parse_mode: ParseMode = ParseMode.MARKDOWN_V2):
        self.text = text() if callable(text) else text
        self.parse_mode = parse_mode


class MessagePicture:
    def __init__(self,
                 picture_file_disk_source: Optional[AnyStr] = None,
                 picture_file_telegram_id: Optional[AnyStr] = None):
        if picture_file_disk_source is None and picture_file_telegram_id is None:
                raise ValueError('File disk source and file telegram id cannot both be none')
        self.picture_file_disk_source = picture_file_disk_source
        self.picture_file_telegram_id = picture_file_telegram_id


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

    def get_actions(self) -> 'Optional[List[Action]]':
        return self._actions if self._actions is not None else []


class MessageKeyboard:

    def __init__(self,
                 buttons: Union[
                     List[MessageKeyboardButton | Callable[..., MessageKeyboardButton]],
                     Choice[List[MessageKeyboardButton | Callable[..., MessageKeyboardButton]]],
                     Callable[..., List[MessageKeyboardButton | Callable[..., MessageKeyboardButton]]],
                     Callable[..., Choice[List[MessageKeyboardButton | Callable[..., MessageKeyboardButton]]]]
                 ],
                 is_non_keyboard_input_allowed: bool = False):
        self._buttons = buttons
        self.is_non_keyboard_input_allowed = is_non_keyboard_input_allowed

    def get_buttons(self,
                    scope: 'Scope',
                    user: 'User') -> List[MessageKeyboardButton]:
        buttons = self._buttons(scope, user) if callable(self._buttons) else self._buttons
        buttons = buttons.get(scope, user) if isinstance(buttons, Choice) else buttons
        buttons = [button(scope, user) if callable(button) else button for button in buttons]
        return buttons


class Message:

    def __init__(self,
                 text: Optional[
                    Union[
                         MessageText | Choice[MessageText],
                         Callable[..., MessageText] | Choice[Callable[..., MessageText]]
                    ]
                 ] = None,
                 picture: Optional[MessagePicture | Choice[MessagePicture]] = None,
                 keyboard: Optional[MessageKeyboard | Choice[MessageKeyboard]] = None):
        self._text = text
        self._picture = picture
        self._keyboard = keyboard

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
            return self._picture.get(scope, user)
        else:
            return self._picture

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
