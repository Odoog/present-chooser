import logging
from typing import List

from data_access_layer.database import Database
from models.good import Good


class Repository:

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
        # logging.info("get_good_by_id | Получаю товар по id = {} получил = {}".format(ind, goods[ind - 1].name))
        return goods[ind - 1]

    @staticmethod
    def clear_good_rating(scope, user):
        user.change_variable("goods_rating", {})
        user.change_variable("categories_rating", {})

    @staticmethod
    def change_good_rating(scope, user, ind, iter_value):
        if (goods_rating := user.get_variable("goods_rating")) is None:
            user.change_variable("goods_rating", {})
            goods_rating = {}

        if ind in goods_rating:
            goods_rating[ind] += iter_value
        else:
            goods_rating[ind] = iter_value

        user.change_variable("goods_rating", goods_rating)

        logging.info("change_good_rating | Меняю рейтинг категории у товара " + Repository.get_good_by_id(
            ind).name + " с категорией " + Repository.get_good_by_id(ind).category)

        category = Repository.get_good_by_id(ind).category

        if (categories_rating := user.get_variable("categories_rating")) is None:
            user.change_variable("categories_rating", {})
            categories_rating = {}

        if category in categories_rating:
            categories_rating[category] += iter_value
        else:
            categories_rating[category] = iter_value

        logging.info("change_good_rating | Новый рейтинг этой категории стал: {}".format(str(categories_rating[category])))

        user.change_variable("categories_rating", categories_rating)

    @staticmethod
    def get_good_category_rating(scope, user, ind):

        category = Repository.get_good_by_id(ind).category

        if (categories_rating := user.get_variable("categories_rating")) is None:
            user.change_variable("categories_rating", {})
            categories_rating = {}

        if category in categories_rating:
            return categories_rating[category]
        else:
            categories_rating[category] = 0
            return 0