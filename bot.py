import logging
from typing import AnyStr

from telegram.ext import MessageHandler, Filters, Updater
from telegram.replykeyboardmarkup import ReplyKeyboardMarkup

from global_transferable_entities.scope import Scope
from global_transferable_entities.user import User


class Bot:

    def __init__(self,
                 token: AnyStr,
                 scope: Scope):
        self._updater = Updater(token)
        self._dispatcher = self._updater.dispatcher
        self._scope = scope

        self._dispatch()

    def _dispatch(self):
        message_handler = MessageHandler(Filters.text | Filters.command, self.process_message)
        self._dispatcher.add_handler(message_handler)
        logging.info("Bot dispatched")

    def start_polling(self,
                      poll_interval = 5,
                      poll_timeout = 3):
        self._updater.start_polling(poll_interval=poll_interval,
                                    timeout=poll_timeout)
        logging.info('Bot polling started')

    def process_message(self,
                        update,
                        context):
        update = update

        update_text = update.message.text
        user_chat_id = update.effective_chat.id

        logging.info("Get the message with text : {}".format(update_text))

        user = User(user_chat_id)
        current_user_stage = self._scope.get_stage(user.get_current_stage_name())

        transition_stage_message = current_user_stage.process_input(update_text, self._scope, user)
        transition_stage_message_text = transition_stage_message.get_text(self._scope, user)
        transition_stage_message_keyboard = transition_stage_message.get_keyboard(self._scope, user)

        if transition_stage_message_keyboard is None:
            message_reply_markup = None
        else:
            keyboard_buttons = transition_stage_message_keyboard.get_buttons(self._scope, user)
            keyboard_buttons_strings = [button.get_text(self._scope, user) for button in keyboard_buttons]
            message_reply_markup = ReplyKeyboardMarkup([keyboard_buttons_strings],
                                                       resize_keyboard=True,
                                                       one_time_keyboard=True)

        context.bot.send_message(chat_id=user_chat_id,
                                 text=transition_stage_message_text.text,
                                 parse_mode=transition_stage_message_text.parse_mode,
                                 reply_markup=message_reply_markup)

