from typing import List, AnyStr, Dict, Any, Optional

from data_access_layer.database import Database
from state_constructor_parts.stats import Stats


class User:
    _stage_history: List[AnyStr]
    _user_variables: Dict[AnyStr, AnyStr]
    _statistics: Optional[List[Stats]]

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

    def try_get_variable(self,
                         variable_name: AnyStr,
                         default_value: Any):
        value = self.get_variable(variable_name)
        if value is None:
            self.change_variable(variable_name, default_value)
            return default_value
        return value

    def get_variable(self,
                     variable_name: str):
        try:
            self.update_info()
            return self._user_variables[variable_name]
        except Exception:
            return None

    def delete(self):
        Database.delete_user(self.chat_id)

    def get_statistics(self, scope, user):
        return self._statistics

    def count_statistics(self,
                         input_string: AnyStr,
                         scope: 'Scope',
                         user: 'User',
                         stage: 'Stage'):
        if statistics := self.get_statistics(scope, user):
            for statistic in statistics:
                statistic.step(scope, user, stage, input_string)
