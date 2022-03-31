import json
import logging
from datetime import datetime, timedelta

from models.good import Good
import pygsheets


class SheetsClient:

    def __init__(self, table_key):
        self.client = pygsheets.authorize(service_file='account_credentials.json')
        self.sheet = self.client.open_by_key(table_key)
        self.db_sheet = self.sheet.worksheet_by_title('База товаров')
        self.attributes_sheet = self.sheet.worksheet_by_title('Атрибуты')
        self.goods = []
        self.last_time_update = datetime.min
        self.last_time_update_cat = datetime.min
        self.goods_table_changes = []
        self.goods_table_changes_count = 0
        self.goods_category_rating = {}
        self.goods_category_rating_changes = {}
        self.goods_category_rating_changes_count = 0

    def get_all_goods(self):
        if datetime.now() - self.last_time_update > timedelta(hours=1):
            self.last_time_update = datetime.now()
            self.goods = []
            values = self.db_sheet.get_all_values(returnas='matrix')
            for key, row in enumerate(values[1:]):
                if row[0] == "" or row[0] is None:
                    break
                good = Good(key + 1, *row[0:18])
                #current_prices = good.get_current_prices()
                #if current_prices is not None:
                #    for price_key, price in enumerate(current_prices):
                #        self.db_sheet.update_value((key + 2, 31 + price_key), price)
                self.goods.append(good)
        return self.goods

    def get_goods_category_rating(self):
        if datetime.now() - self.last_time_update_cat > timedelta(hours=1):
            self.last_time_update = datetime.now()
            self.goods_category_rating = {}
            values = self.attributes_sheet.get_all_values(returnas='matrix')
            cat_names = values[19]
            cat_rating = values[20]
            for key, cat_name in enumerate(cat_names):
                self.goods_category_rating[cat_name] = int(cat_rating[key] if cat_rating[key] != "" else 0)
        return self.goods_category_rating

    def get_good_by_id(self, ind) -> Good:
        goods = self.get_all_goods()
        return goods[ind - 1]

    def change_good_rating(self, scope, user, ind, iter_value):
        if (goods_rating := scope.try_get_variable("goods_rating")) is None:
            scope.change_variable("goods_rating", {})
            goods_rating = {}

        if ind in goods_rating:
            goods_rating[ind] += iter_value
        else:
            goods_rating[ind] = iter_value

        scope.change_variable("goods_rating", goods_rating)

        category = self.get_good_by_id(ind).category

        if (categories_rating := scope.try_get_variable("categories_rating")) is None:
            scope.change_variable("categories_rating", {})
            categories_rating = {}

        if category in categories_rating:
            categories_rating[category] += iter_value
        else:
            categories_rating[category] = iter_value

        scope.change_variable("categories_rating", categories_rating)
