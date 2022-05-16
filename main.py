import logging
import os
import random

from telegram import ParseMode

from data_access_layer.repository import Repository
from global_transferable_entities.user import User
from site_worker.worker import Worker
from state_constructor_parts.action import ActionChangeUserVariable, ActionChangeUserVariableToInput, ActionChangeStage, \
    Action, PrerequisiteAction
from bot import Bot
from message_parts.message import Message, MessageKeyboard, MessageKeyboardButton, MessagePicture
from global_transferable_entities.scope import Scope
from state_constructor_parts.stage import Stage
from data_access_layer.google_tables import SheetsClient, LocalBrandSheetClient
from statistics_entities.custom_stats import UserStatsCyclesFinishCount, UserStatsCyclesStartCount
from statistics_entities.stage_stats import StageStatsVisitCount
from statistics_entities.user_stats import UserStatsVisitCount, UserStatsCurrentStage

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info("Program started")

    # --- Helper methods ---

    def get_all_relevant_goods(scope, user):
        logging.info("get_all_relevant_goods | Запускаю фильтр подарков")
        all_goods = Repository.get_all_goods()
        logging.info("get_all_relevant_goods | Все подарки в системе : " + " ".join([str(good.ind) for good in all_goods]))
        all_goods = list(filter(lambda good: user.get_variable("age") in good.age or good.is_universal, all_goods))
        logging.info("get_all_relevant_goods | Сортировка по возрасту : " + " ".join([str(good.ind) for good in all_goods]))
        all_goods = list(filter(lambda good: user.get_variable("sex") in good.sex or good.is_universal, all_goods))
        logging.info("get_all_relevant_goods | Сортировка по полу : " + " ".join([str(good.ind) for good in all_goods]))
        all_goods = list(filter(lambda good: int(user.get_variable("spend").split('-')[0])
                                             <= good.price_actual
                                             <= int(user.get_variable("spend").split('-')[1]),
                                all_goods))
        logging.info("get_all_relevant_goods | Сортировка по цене : " + " ".join([str(good.ind) for good in all_goods]))
        if user.get_variable("age") == "ребенку":
            all_goods = list(filter(lambda good: user.get_variable("age2") in good.age2 or good.is_universal, all_goods))
            logging.info("get_all_relevant_goods | Сортировка по второму возрасту для ребенка : " + " ".join([str(good.ind) for good in all_goods]))
        if user.get_variable("age") == "взрослому":
            all_goods = list(filter(lambda good: user.get_variable("receiver") in good.receiver or good.is_universal, all_goods))
            logging.info("get_all_relevant_goods | Сортировка по получателю для возрослого : " + " ".join([str(good.ind) for good in all_goods]))
        all_goods = list(filter(lambda good: user.get_variable("reason") in good.reason or good.is_universal_reason and (user.get_variable("reason") == "Другой повод" or user.get_variable("reason") is None),
                                all_goods))
        logging.info("get_all_relevant_goods | Сортировка по поводу : " + " ".join([str(good.ind) for good in all_goods]))
        all_goods = sorted(all_goods, key=lambda good: (-Repository.get_good_category_rating(scope, user, good.ind), random.random()))
        logging.info("get_all_relevant_goods | Подарки после сортировки : " + " ".join([str(good.ind) + " " + good.category + "\n" for good in all_goods]))
        return all_goods


    def sort_goods(scope, user):
        good_id = user.get_variable("good_id")
        goods = Repository.get_goods(user.get_variable("show_list"))
        # Сортируем только те которые пользователь еще не просмотрел
        # logging.info("goods were: " + ",".join([str(good.ind) + " " + good.category + " " + str(Repository.get_good_category_rating(scope, user, good.ind)) + "\n" for good in goods]))
        goods = goods[:good_id] + sorted(goods[good_id:],
                                         key=lambda good: (-Repository.get_good_category_rating(scope, user, good.ind), random.random()))
        # logging.info("goods are: " + ",".join([str(good.ind) + " " + good.category + " " + str(Repository.get_good_category_rating(scope, user, good.ind)) + "\n" for good in goods]))
        user.set_variable("show_list", [good.ind for good in goods])


    def generate_text_for_current_good(_, user):
        good = Repository.get_good_by_id(int(user.get_variable("showing_id")))
        return "{} / {} {}\nМагазин: {}\nЦена: {}₽".format(
            good.name,
            good.brand,
            "🇷🇺" if good.is_local_brand else "",
            good.shop,
            good.price_actual)

    # --- State constructor ---

    Stage.set_common_statistics([StageStatsVisitCount()])
    User.set_common_statistics([UserStatsVisitCount(),
                                UserStatsCurrentStage()])

    _scope = Scope([

        Stage(name="NewUser",
              user_input_actions=[ActionChangeStage("Opening")]),

        Stage(name="Opening",
              message=Message(
                  text="Привет! Я бот из компании Symbol, моя работа — помогать людям выбирать классные подарки. \n\n"
                       "Кому вы ищете подарок?",
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
              user_input_actions=[ActionChangeStage("AskingForSex"),
                                  Action(lambda scope, user, _, __: Repository.clear_good_rating(scope, user))],  # Обнуляем рейтинг подарков для пользователя.
              statistics=[UserStatsCyclesStartCount()]),

        Stage(name="AskingForSex",
              message=Message(
                  text="Выберите пол",
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text=lambda _, user: "Мужчине" if user.get_variable("age") == "взрослому" else "Мальчику",
                              actions=[ActionChangeUserVariable("sex", "мальчику")]),
                          MessageKeyboardButton(
                              text=lambda _, user: "Женщине" if user.get_variable("age") == "взрослому" else "Девочке",
                              actions=[ActionChangeUserVariable("sex", "девочке")])
                      ],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=lambda _, user:
              {
                  "подростку": [ActionChangeStage("AskingForMoney")],
                  "ребенку": [ActionChangeStage("AskingForAge2")],
                  "взрослому": [ActionChangeStage("AskingForReceiver")]
              }.get(user.get_variable("age"))),

        Stage(name="AskingForAge2",
              message=Message(
                  text="Выберите возраст",
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
              user_input_actions=[ActionChangeStage("AskingForMoney")]),

        Stage(name="AskingForReceiver",
              message=Message(
                  text="Выберите получателя",
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
              user_input_actions=[ActionChangeStage("AskingForMoney")]),

        Stage(name="AskingForMoney",
              message=Message(
                  text="Сколько готовы потратить?",
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
              user_input_actions=lambda _, user:
                  {
                      "Себе": [ActionChangeStage("ReadyToShow")],
                  }.get(user.get_variable("receiver"), [ActionChangeStage("AskingForReason")])),

        Stage(name="AskingForReason",
              message=Message(
                  text="Хотите указать повод для подарка?",
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text="Да, это важно",
                              actions=[ActionChangeStage("AskingForReason2")]),
                          MessageKeyboardButton(
                              text="Нет",
                              actions=[ActionChangeUserVariable("reason", None),
                                       ActionChangeStage("ReadyToShow")]),
                      ],
                      is_non_keyboard_input_allowed=False))),

        Stage(name="AskingForReason2",
              message=Message(
                  text="Выберите повод для подарка?",
                  keyboard=MessageKeyboard(
                      buttons=lambda scope, user: [
                          MessageKeyboardButton(text=txt) for txt in ["8 Марта",
                                                                      "День рождения",
                                                                      "23 Февраля",
                                                                      "14 Февраля",
                                                                      "Новый год",
                                                                      "Свадьба, годовщина",
                                                                      "Рождение ребенка",
                                                                      "Другой повод"]
                          if not (user.get_variable("sex") == "мальчику" and txt in ["8 Марта"]) and not (user.get_variable("sex") == "девочке" and txt in ["23 Февраля"])
                      ],
                      buttons_layout=[2, 2, 2, 2],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=[ActionChangeUserVariableToInput("reason"),
                                  ActionChangeStage("ReadyToShow")]),

        Stage(name="ReadyToShow",
              message=Message(
                  text=lambda scope, user:
                      "Отлично! У меня для вас много интересных вариантов — выбирайте :) \n\nЗапоминать "
                      "ничего не нужно — когда вы нажмете \"Стоп\", я покажу вам все подарки, который вам"
                      " понравились."
                      if len(get_all_relevant_goods(scope, user)) > 0 else
                      "Подарков, подходящих под ваши критерии, пока нет :( "
                      "\nПопробуйте изменить параметры — например, бюджет",
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(text="Хорошо")
                      ],
                      is_non_keyboard_input_allowed=False)),
              user_input_actions=lambda _, user:
                                        {
                                            True: [
                                                ActionChangeStage("ShowingGoodPre"),
                                                ActionChangeUserVariable("good_id", 0),
                                                ActionChangeUserVariable("show_list", lambda scope, user: [good.ind for good in get_all_relevant_goods(scope, user)]),
                                                ActionChangeUserVariable("fav_list", []),
                                                ActionChangeUserVariable("showing_id", lambda _, user: user.get_variable("show_list")[user.get_variable("good_id")])
                                            ],
                                            False: [ActionChangeStage("Opening")]
                                        }.get(len(get_all_relevant_goods(_scope, user)) > 0)),

        Stage(name="ShowingGoodPre",
              message=Message(text="Выбирайте 😇"),
              prerequisite_actions=[PrerequisiteAction(lambda scope, user, sent_message, _: user.set_variable("message_to_delete_after_id",
                                                                                                              sent_message.message_id))],
              user_input_actions=[ActionChangeStage("ShowingGood")],
              is_gatehouse=True),

        Stage(name="ShowingGood",
              message=Message(
                  text=lambda scope, user: generate_text_for_current_good(scope, user),
                  picture=lambda scope, user: MessagePicture(
                      picture_file_link=Repository.get_good_by_id(user.get_variable("showing_id")).photo_link),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text="Нравится",
                              actions=[ActionChangeUserVariable("fav_list", lambda _, user: user.get_variable("fav_list") + [user.get_variable("show_list")[user.get_variable("good_id") - 1]])]),
                          MessageKeyboardButton(text="Не подходит"),
                          MessageKeyboardButton(
                              text="Стоп",
                              actions=[ActionChangeStage("ShowingFinish"),
                                       ActionChangeUserVariable("showing_limit_exceed", False),
                                       Action(lambda scope, user, _, bot: bot.delete_message(chat_id=user.chat_id,
                                                                                             message_id=user.get_variable("message_to_delete_after_id")))])
                      ],
                      is_inline_keyboard=True,
                      buttons_layout=[2, 1],
                      is_non_keyboard_input_allowed=False),
                  should_replace_last_message=True),
              user_input_actions=lambda scope, user:{
                         True: [
                             Action(lambda scope, user, input, _: Repository.change_good_rating(scope,
                                                                                                user,
                                                                                                user.get_variable("showing_id"),
                                                                                                1 if input == "Нравится" else -1)),
                             ActionChangeUserVariable("good_id", lambda scope, user: user.get_variable("good_id") + 1),
                             Action(lambda scope, user, _, __: sort_goods(scope, user)),
                             # Сортируем оставшиеся для показа товары по рейтингу
                             ActionChangeUserVariable("showing_id",
                                                      lambda _, user: user.get_variable("show_list")[user.get_variable("good_id")])
                         ],
                         False: [
                             ActionChangeStage("ShowingFinish"),
                             ActionChangeUserVariable("showing_limit_exceed", True),
                             Action(lambda scope, user, _, bot: bot.delete_message(chat_id=user.chat_id,
                                                                                   message_id=user.get_variable("message_to_delete_after_id")))
                         ]
                     }.get(user.get_variable("good_id") + 1 < len(user.get_variable("show_list")))),

        Stage(name="ShowingFinish",
              message=Message(
                  text=lambda scope, user:
                      ("Я показал всё, что смог подобрать для вас:)\n" if user.get_variable("showing_limit_exceed") else "") +
                      "Все подарки, которые вам понравились, собраны [здесь]({}) :) Хорошего дня!".format(
                          worker.build_site(user.get_variable("fav_list")))
                      if len(user.get_variable("fav_list")) > 0
                      else "Жаль, что мы ничего не смогли для вас подобрать 😔",
                  text_parse_mode=ParseMode.MARKDOWN,
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(text="Выбрать еще один подарок",
                                                actions=[ActionChangeStage("Opening")])
                      ],
                      is_non_keyboard_input_allowed=False),
                  should_delete_last_message=True),
              statistics=[UserStatsCyclesFinishCount()])

    ], main_stage_name="MainMenu")

    SheetsClient(os.environ['sheets_token']).synchronize()
    LocalBrandSheetClient(os.environ['local_brand_sheet_token']).synchronize()

    worker = Worker()
    worker.generate_goods_files()

    Bot(os.environ['telegram_token'], _scope).start_polling(poll_interval=2,
                                                            poll_timeout=1)
