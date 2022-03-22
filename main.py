import logging
from datetime import datetime

from state_constructor_parts.action import ActionChangeUserVariable, ActionChangeUserVariableToInput, ActionChangeStage, Action, \
    ActionBackToMainStage
from bot import Bot
from state_constructor_parts.filter import IntNumberFilter
from message_parts.message import Message, MessageText, SimpleTextMessage, MessageKeyboard, MessageKeyboardButton
from global_transferable_entities.scope import Scope
from state_constructor_parts.stage import Stage
from google_tables import SheetsClient

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info("Program started")

    # Example of using state constructor to create a bot. 

    scope = Scope([
        Stage(name="NewUser",
              message=Message(
                  text=MessageText(
                      "Привет! Я бот из компании Symbol, моя работа - помогать людям выбирать классные подарки. \n Кому вы ищете подарок?"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text="Ребенку",
                              actions=[ActionChangeUserVariable("age", "kid")]),
                          MessageKeyboardButton(
                              text="Подростку",
                              actions=[ActionChangeUserVariable("age", "teenager")]),
                          MessageKeyboardButton(
                              text="Взрослому",
                              actions=[ActionChangeUserVariable("age", "adult")])
                      ],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=[ActionChangeStage("AskingForSex")]),

        Stage(name="AskingForSex",
              message=Message(
                  text=MessageText("Выберите пол"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text=lambda scope, user: "Мужчине" if user.get_variable("age") == "adult" else "Мальчику",
                              actions=[ActionChangeUserVariable("sex", "boy"),
                                       lambda scope, user: ActionChangeStage("AskingForMoney") if user.get_variable(
                                           "age") == "teenager" else None]),
                          MessageKeyboardButton(
                              text=lambda scope, user: "Женщине" if user.get_variable("age") == "adult" else "Девочке",
                              actions=[ActionChangeUserVariable("sex", "girl")])
                      ],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=[ActionChangeStage("AskingForAdditionalInfo")]),

        Stage(name="AskingForAdditionalInfo",
              message=Message(
                  text=lambda scope, user: MessageText("Выберите возраст") if user.get_variable("age") == "kid" else MessageText("Кому вы хотите сделать подарок?"),
                  keyboard=MessageKeyboard(
                      buttons=lambda scope, user:
                          [
                              MessageKeyboardButton(
                                  text="4-7 лет",
                                  actions=[ActionChangeUserVariable("age2", "4-7")]),
                              MessageKeyboardButton(
                                  text="8-12 лет",
                                  actions=[ActionChangeUserVariable("age2", "8-12")])
                          ]
                          if user.get_variable("age") == "kid" else
                          [
                              MessageKeyboardButton(
                                  text="Любимому человеку",
                                  actions=[ActionChangeUserVariable("reciever", "lover")]),
                              MessageKeyboardButton(
                                  text="Другу, родственнику",
                                  actions=[ActionChangeUserVariable("reciever", "friend")]),
                              MessageKeyboardButton(
                                  text="Коллеге, руководителю",
                                  actions=[ActionChangeUserVariable("reciever", "colleague")]),
                              MessageKeyboardButton(
                                  text="Себе",
                                  actions=[ActionChangeUserVariable("reciever", "self")])
                          ],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=[ActionChangeStage("AskingForMoney")]),

        Stage(name="AskingForMoney",
              message=Message(
                  text=MessageText("Деньги"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text="Начало процесса",
                              actions=[ActionChangeUserVariable("process_start_time", str(datetime.now())),
                                       ActionChangeStage("Process_AskingForProductType")])
                      ],
                      is_non_keyboard_input_allowed=False))),
    ], main_stage_name="MainMenu")

    #sheets = SheetsClient('1vDOQoN7a9Bk016txadTRvW74A0RcTr1WPikatIL3tVU')
    #sheets.get_all_goods()

    #token = "YOUR_TELEGRAM_TOKEN_HERE"

    Bot(token, scope).start_polling(poll_interval=2,
                                    poll_timeout=1)