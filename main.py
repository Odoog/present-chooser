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

    # Example of creating functions called by state constructor. 
    
    def get_possible_product_types():
        return ["Type1", "Type2", "Type3"]


    def get_possible_product_types_keyboard_buttons(scope, user):
        return [MessageKeyboardButton(prod_type) for prod_type in get_possible_product_types()]


    def get_possible_product_articles_keyboard_buttons(scope, user):
        chosen_product = user.get_variable("process_product_type")
        possible_articles = ["Article1", "Article2"]
        return [MessageKeyboardButton(article) for article in possible_articles]


    def get_possible_operations_keyboard_buttons(scope, user):
        chosen_product = user.get_variable("process_product_type")
        possible_operations = ["Operation1", "Operation2"]
        return [MessageKeyboardButton(operation) for operation in possible_operations]


    def save_process(scope, user, input_string):
        user_name = user.get_variable("name")
        process_start_time = user.get_variable("process_start_time")
        process_product_type = user.get_variable("process_product_type")
        process_product_article = user.get_variable("process_product_article")
        process_operation = user.get_variable("process_operation")
        process_operations_count = user.get_variable("process_operations_count")


    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info("Program started")

    # Example of using state constructor to create a bot. 

    scope = Scope([
        Stage(name = "NewUser",
              user_input_actions=[ActionChangeStage("AskingForName")]),

        Stage(name="AskingForName",
              message=SimpleTextMessage("Введите ваше имя"),
              user_input_actions=[ActionChangeUserVariableToInput("name"),
                                  ActionChangeStage("MainMenu")]),

        Stage(name="MainMenu",
              message=Message(
                  text=MessageText("Выберите опцию"),
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(
                              text="Начало процесса",
                              actions=[ActionChangeUserVariable("process_start_time", str(datetime.now())),
                                       ActionChangeStage("Process_AskingForProductType")])
                      ],
                      is_non_keyboard_input_allowed=False))),

        Stage(name="Process_AskingForProductType",
              message=Message(
                  text=MessageText("Выберите тип продукции"),
                  keyboard=MessageKeyboard(buttons=get_possible_product_types_keyboard_buttons,
                                           is_non_keyboard_input_allowed=False)),
              user_input_actions=[ActionChangeUserVariableToInput("process_product_type"),
                                  ActionChangeStage("Process_AskingForProductArticle")]),

        Stage(name="Process_AskingForProductArticle",
              message=Message(text=MessageText("Выберите артикул"),
                              keyboard=MessageKeyboard(buttons=get_possible_product_articles_keyboard_buttons,
                                                       is_non_keyboard_input_allowed=False)),
              user_input_actions=[ActionChangeUserVariableToInput("process_product_article"),
                                  ActionChangeStage("Process_AskingForOperation")]),

        Stage(name="Process_AskingForOperation",
              message=Message(text=MessageText("Выберите вид операции"),
                              keyboard=MessageKeyboard(buttons=get_possible_operations_keyboard_buttons,
                                                       is_non_keyboard_input_allowed=False)),
              user_input_actions=[ActionChangeUserVariableToInput("process_operation"),
                                  ActionChangeStage("Process_AskingForOperationsCount")]),

        Stage(name="Process_AskingForOperationsCount",
              message=SimpleTextMessage("После окончания процесса введите количество операций"),
              user_input_actions=[ActionChangeUserVariableToInput("process_operations_count"),
                                  Action(save_process),
                                  ActionBackToMainStage()],
              user_input_filter=IntNumberFilter(not_passed_reason_message="Введённое значение не является числом"))
    ], main_stage_name="MainMenu")

    sheets = SheetsClient('1vDOQoN7a9Bk016txadTRvW74A0RcTr1WPikatIL3tVU')
    sheets.get_all_goods()

    token = "YOUR_TELEGRAM_TOKEN_HERE"

    #Bot(token, scope).start_polling(poll_interval=2,
    #                                poll_timeout=1)
    #
