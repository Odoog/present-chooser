import json
import logging
import os
import random
from datetime import datetime

from telegram import ParseMode

from site_worker.worker import Worker
from state_constructor_parts.action import ActionChangeUserVariable, ActionChangeUserVariableToInput, ActionChangeStage, \
    Action, \
    ActionBackToMainStage
from bot import Bot
from state_constructor_parts.filter import IntNumberFilter
from message_parts.message import Message, MessageText, SimpleTextMessage, MessageKeyboard, MessageKeyboardButton, \
    MessagePicture
from global_transferable_entities.scope import Scope
from state_constructor_parts.stage import Stage
from google_tables import SheetsClient
from state_constructor_parts.stats import StageStatsVisitCount, UserStatsVisitCount
from typing_module_extensions.choice import Choice

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info("Program started")

    # Example of using state constructor to create a bot.

    def get_all_relevant_goods(scope, user):
        all_goods = sheets.get_all_goods()
        all_goods = list(filter(lambda good: user.get_variable("age") in good.age or good.is_universal == "TRUE", all_goods))
        all_goods = list(filter(lambda good: user.get_variable("sex") in good.sex or good.is_universal == "TRUE", all_goods))
        all_goods = list(filter(lambda good: int(user.get_variable("spend").split('-')[0]) <= int("".join(filter(str.isdigit, good.price_actual))) <= int(user.get_variable("spend").split('-')[1]), all_goods))
        if user.get_variable("age") == "ребенку":
            all_goods = list(
                filter(lambda good: user.get_variable("age2") in good.age2 or good.is_universal == "TRUE", all_goods))
        if user.get_variable("age") == "взрослому":
            all_goods = list(
                filter(lambda good: user.get_variable("receiver") in good.receiver or good.is_universal == "TRUE", all_goods))
        all_goods = list(
            filter(lambda good: user.get_variable("reason") in good.reason or
                                good.is_universal_reason == "TRUE" and (user.get_variable("reason") == "Другой повод" or user.get_variable("reason") is None),
                   all_goods))

        return sorted(all_goods, key=lambda good: (-sheets.get_good_category_rating(scope, user, good.ind), random.random()))


    def generate_text_for_current_good(scope, user):
        good = sheets.get_good_by_id(int(user.get_variable("showing_id")))
        return "{} / {} {}\nМагазин: {}\nЦена: {}₽".format(
            good.name,
            good.brand,
            "🇷🇺" if good.is_local_brand else "",
            good.shop,
            good.price_actual)


    scope = Scope([
        Stage(name="NewUser",
              user_input_actions=[ActionChangeStage("Opening")]),
        Stage(name="Opening",
              message=Message(
                  text=MessageText(
                      "Привет! Я бот из компании Symbol, моя работа — помогать людям выбирать классные подарки. \n\n"
                      "Кому вы ищете подарок?"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text="Ребенку",
                              actions=[ActionChangeUserVariable("age", "ребенку")]),
                          MessageKeyboardButton(
                              text="Подростку",
                              actions=[ActionChangeUserVariable("age", "подростку")]),
                          MessageKeyboardButton(
                              text="Взрослому",
                              actions=[ActionChangeUserVariable("age", "взрослому")])
                      ],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=[ActionChangeStage("AskingForSex")],
              statistics=[StageStatsVisitCount(),
                          UserStatsVisitCount()]),

        Stage(name="AskingForSex",
              message=Message(
                  text=MessageText("Выберите пол"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text=lambda scope, user: "Мужчине" if user.get_variable(
                                  "age") == "взрослому" else "Мальчику",
                              actions=[ActionChangeUserVariable("sex", "мальчику")]),
                          MessageKeyboardButton(
                              text=lambda scope, user: "Женщине" if user.get_variable(
                                  "age") == "взрослому" else "Девочке",
                              actions=[ActionChangeUserVariable("sex", "девочке")])
                      ],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=Choice(
                  lambda scope, user: user.get_variable("age"),
                  {
                      "подростку": [ActionChangeStage("AskingForMoney"), ActionChangeUserVariable("spend", [])],
                      "ребенку": [ActionChangeStage("AskingForAge2")],
                      "взрослому": [ActionChangeStage("AskingForReceiver")]
                  }),
              statistics=[StageStatsVisitCount(),
                          UserStatsVisitCount()]),

        Stage(name="AskingForAge2",
              message=Message(
                  text=MessageText("Выберите возраст"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text="4-7 лет",
                              actions=[ActionChangeUserVariable("age2", "4-7 лет")]),
                          MessageKeyboardButton(
                              text="8-12 лет",
                              actions=[ActionChangeUserVariable("age2", "8-12 лет")])
                      ],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=[ActionChangeStage("AskingForMoney"), ActionChangeUserVariable("spend", [])],
              statistics=[StageStatsVisitCount(),
                          UserStatsVisitCount()]),

        Stage(name="AskingForReceiver",
              message=Message(
                  text=MessageText("Выберите получателя"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text="Любимому человеку",
                              actions=[ActionChangeUserVariable("receiver", "Любимому человеку")]),
                          MessageKeyboardButton(
                              text="Другу, родственнику",
                              actions=[ActionChangeUserVariable("receiver", "Другу, родственнику")]),
                          MessageKeyboardButton(
                              text="Коллеге, руководителю",
                              actions=[ActionChangeUserVariable("receiver", "Коллеге, руководителю")]),
                          MessageKeyboardButton(
                              text="Себе",
                              actions=[ActionChangeUserVariable("receiver", "Себе")])
                      ],
                      buttons_layout=[2, 2],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=[ActionChangeStage("AskingForMoney"), ActionChangeUserVariable("spend", [])],
              statistics=[StageStatsVisitCount(),
                          UserStatsVisitCount()]),

        Stage(name="AskingForMoney",
              message=Message(
                  text=MessageText("Сколько готовы потратить?"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text="До 3000 рублей",
                              actions=[ActionChangeUserVariable("spend", "0-3000")]),
                          MessageKeyboardButton(
                              text="От 3000 до 8000 рублей",
                              actions=[ActionChangeUserVariable("spend", "3000-8000")]),
                          MessageKeyboardButton(
                              text="Больше 8000 рублей",
                              actions=[ActionChangeUserVariable("spend", "8000-999999")])
                      ],
                      buttons_layout=[2, 2, 1],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=Choice(
                  lambda scope, user: user.get_variable("receiver"),
                  {
                      "Себе": [ActionChangeStage("ReadyToShow")],
                      "_": [ActionChangeStage("AskingForReason")],
                  }),
              statistics=[StageStatsVisitCount(),
                          UserStatsVisitCount()]),

        Stage(name="AskingForReason",
              message=Message(
                  text=MessageText("Хотите указать повод для подарка?"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text="Да, это важно",
                              actions=[ActionChangeStage("AskingForReason2")]),
                          MessageKeyboardButton(
                              text="Нет",
                              actions=[ActionChangeStage("ReadyToShow")]),
                      ],
                      is_non_keyboard_input_allowed=False)),
              statistics=[StageStatsVisitCount(),
                          UserStatsVisitCount()]),

        Stage(name="AskingForReason2",
              message=Message(
                  text=MessageText("Выберите повод для подарка?"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(text="8 Марта"),
                          MessageKeyboardButton(text="День рождения"),
                          MessageKeyboardButton(text="23 Февраля"),
                          MessageKeyboardButton(text="14 Февраля"),
                          MessageKeyboardButton(text="Новый год"),
                          MessageKeyboardButton(text="Свадьба, годовщина"),
                          MessageKeyboardButton(text="Рождение ребенка"),
                          MessageKeyboardButton(text="Другой повод"),
                      ],
                      buttons_layout=[2, 2, 2, 2],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=[ActionChangeUserVariableToInput("reason"),
                                  ActionChangeStage("ReadyToShow")],
              statistics=[StageStatsVisitCount(),
                          UserStatsVisitCount()]),

        Stage(name="ReadyToShow",
              message=Message(
                  text=lambda scope, user: MessageText("Отлично! У меня для вас много интересных варинтов — выбирайте :) \n\nЗапоминать "
                                                       "ничего не нужно — когда вы нажмете \"Стоп\", я покажу вам все подарки, который вам"
                                                       " понравились.") if len(get_all_relevant_goods(scope, user)) > 0 else
                                            MessageText("Подарков, подходящих под ваши критерии, пока нет :( "
                                                        "\nПопробуйте изменить параметры — например, бюджет"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(text="Хорошо")
                      ],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=Choice(lambda scope, user: len(get_all_relevant_goods(scope, user)) > 0,
                                        {
                                            True: [
                                                ActionChangeStage("ShowingGood"),
                                                ActionChangeUserVariable("good_id", "0"),
                                                ActionChangeUserVariable("show_list", lambda scope, user: json.dumps(
                                                    [good.ind for good in get_all_relevant_goods(scope, user)])),
                                                ActionChangeUserVariable("fav_list", "[]"),
                                                ActionChangeUserVariable("showing_id", lambda scope, user:
                                                    json.loads(user.get_variable("show_list"))[int(user.get_variable("good_id"))])
                                            ],
                                            False: [ActionChangeStage("Opening")]
                                        }),
              statistics=[StageStatsVisitCount(),
                          UserStatsVisitCount()]),

        Stage(name="ShowingGood",
              message=Message(
                  text=lambda scope, user: MessageText(generate_text_for_current_good(scope, user)),
                  picture=lambda scope, user: MessagePicture(
                      picture_file_link=sheets.get_good_by_id(int(user.get_variable("showing_id"))).photo_link),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text="Нравится",
                              actions=[Action(lambda scope, user, input: sheets.change_good_rating(scope, user,
                                                                                                   int(user.get_variable(
                                                                                                       "good_id")), 1)),
                                       ActionChangeUserVariable("fav_list", lambda scope, user: json.dumps(
                                           json.loads(user.get_variable("fav_list")) + [
                                               json.loads(user.get_variable("show_list"))[
                                                   int(user.get_variable("good_id")) - 1]]))]),
                          MessageKeyboardButton(
                              text="Не подходит",
                              actions=[Action(lambda scope, user, input: sheets.change_good_rating(scope, user,
                                                                                                   int(user.get_variable(
                                                                                                       "good_id")),
                                                                                                   -1))]),
                          MessageKeyboardButton(
                              text="Стоп",
                              actions=[ActionChangeStage("ShowingFinish")])
                      ],
                      is_inline_keyboard=True,
                      is_non_keyboard_input_allowed=False),
                  should_replace_last_message=True),
              user_input_actions=
              Choice(lambda scope, user: int(user.get_variable("good_id")) + 1 < len(
                  json.loads(user.get_variable("show_list"))),
                     {
                         True: [
                             ActionChangeUserVariable("good_id",
                                                      lambda scope, user: str(int(user.get_variable("good_id")) + 1)),
                             ActionChangeUserVariable("showing_id",
                                                      lambda scope, user: json.loads(user.get_variable("show_list"))[
                                                          int(user.get_variable("good_id"))])
                         ],
                         False: [
                             ActionChangeStage("ShowingLimit")
                         ]
                     }),
              statistics=[StageStatsVisitCount(),
                          UserStatsVisitCount()]),

        Stage(name="ShowingLimit",
              message=Message(
                  text=lambda scope, user: MessageText((
                      "Я показал всё, что смог подобрать для вас :) \n\nВсе подарки, которые вам понравились, собраны [здесь]({})").format(
                      "http://77.87.212.229/present-chooser/build/" + worker.build_site(
                          json.loads(user.get_variable("fav_list"))) + ".html"),
                      ParseMode.MARKDOWN),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(text="Выбрать еще один подарок",
                                                actions=[ActionChangeStage("Opening")])
                      ],
                      is_non_keyboard_input_allowed=False),
                  should_delete_last_message=True),
              statistics=[StageStatsVisitCount(),
                          UserStatsVisitCount()]),

        Stage(name="ShowingFinish",
              message=Message(
                  text=lambda scope, user: MessageText((
                      "Все подарки, которые вам понравились, собраны [здесь]({}) :) Хорошего дня!").format(
                      "http://77.87.212.229/present-chooser/build/" + worker.build_site(
                          json.loads(user.get_variable("fav_list"))) + ".html"),
                      ParseMode.MARKDOWN),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(text="Выбрать еще один подарок",
                                                actions=[ActionChangeStage("Opening")])
                      ],
                      is_non_keyboard_input_allowed=False),
                  should_delete_last_message=True),
              statistics=[StageStatsVisitCount(),
                          UserStatsVisitCount()])

    ], main_stage_name="MainMenu")

    sheets = SheetsClient(os.environ['sheets_token'])
    worker = Worker(sheets)
    worker.generate_goods_files()

    Bot(os.environ['telegram_token'], scope).start_polling(poll_interval=2,
                                                           poll_timeout=1)
