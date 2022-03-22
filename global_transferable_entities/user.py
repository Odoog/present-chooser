from typing import List, AnyStr, Dict

from data_access_layer.database import Database


class User:
    _stage_history: List[AnyStr]
    _user_variables: Dict[AnyStr, AnyStr]

    def __init__(self,
                 chat_id: AnyStr):
        self.chat_id = chat_id

        if not Database.is_user_exist(chat_id):
            Database.add_user(chat_id, ['NewUser'], {})

        self.update_info()

    def update_info(self):
        user_from_db = Database.get_user(self.chat_id)

        self._stage_history = user_from_db['stage_history']
        self._user_variables = user_from_db['user_variables']

    def get_current_stage_name(self) -> AnyStr:
        return self._stage_history[-1]

    def change_stage(self,
                     stage_name: AnyStr):
        self._stage_history.append(stage_name)
        Database.change_user_column(self.chat_id, 'stage_history', self._stage_history)

    def change_variable(self,
                        variable_name: AnyStr,
                        variable_value: AnyStr):
        self._user_variables[variable_name] = variable_value
        Database.change_user_column(self.chat_id, 'user_variables', self._user_variables)

    def get_variable(self,
                     variable_name: str):
        self.update_info()
        return self._user_variables[variable_name]
