import logging
from typing import List

from data_access_layer.database import Database
from models.good import Good


class Repository(Database):

    @staticmethod
    def get_all_goods():
        goods_from_database = Database._run("select * from goods")
        return [Good(*good) for good in goods_from_database]

    @staticmethod
    def get_goods(ids) -> List[Good]:
        return [Repository.get_good_by_id(id) for id in ids]

    @staticmethod
    def get_good_by_id(ind) -> Good:
        goods = Repository.get_all_goods()
        logging.info("get_good_by_id | Получаю товар по id = {} получил = {}".format(ind, goods[ind - 1].name))
        return next(good for good in goods if good.ind == ind)

    @staticmethod
    def clear_good_rating(scope, user):
        user.set_variable("goods_rating", {})
        user.set_variable("categories_rating", {})

    @staticmethod
    def change_good_rating(scope,
                           user,
                           ind,
                           iter_value):

        # Смена рейтинга товара для конкретного пользователя.

        user.change_variable("goods_rating",
                             lambda rating: rating | {ind: rating.get(ind, 0) + iter_value},
                             {})

        logging.info("change_good_rating | Меняю рейтинг категории у товара " + Repository.get_good_by_id(ind).name + " с категорией " + Repository.get_good_by_id(ind).category)

        category = Repository.get_good_by_id(ind).category

        user.change_variable("categories_rating",
                             lambda rating: rating | {category: rating.get(category, 0) + iter_value},
                             {})

        # Смена рейтинга товара в таблице.

        Database._run("update goods set rating = rating + ? where id = ?", (iter_value, ind))

    @staticmethod
    def get_good_category_rating(scope, user, ind):

        category = Repository.get_good_by_id(ind).category

        if (categories_rating := user.get_variable("categories_rating")) is None:
            user.set_variable("categories_rating", {})
            categories_rating = {}

        if category in categories_rating:
            return categories_rating[category]
        else:
            categories_rating[category] = 0
            return 0