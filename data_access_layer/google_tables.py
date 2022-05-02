import json
import logging
from datetime import datetime, timedelta
from typing import List

from data_access_layer.database import Database
from models.good import Good
import pygsheets


class SheetsClient:

    def __init__(self, table_key):
        self.client = pygsheets.authorize(service_file='data_access_layer/account_credentials.json')
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

    def synchronize(self):
        values = self.db_sheet.get_all_values(returnas='matrix')
        Database._run("delete from goods where 1")
        for key, row in enumerate(values[1:]):
            if row[0] == "" or row[0] is None:
                break
            Database._run("insert into goods ( \
                          id, name, brand, shop, price, good_link, good_picture_link, is_local_brand, \
                          is_universal, category, budget, receiver, receiver_sex, receiver_age, \
                          receiver_relative, is_universal_reason, reason, rating) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          [key,
                           row[0],
                           row[1],
                           row[2],
                           int("".join(filter(str.isdigit, row[3]))),  # Цены часто в таблице в формате 1\xa0611, поэтому убираем все лишнее.
                           row[4],
                           row[5],
                           row[6] == "TRUE",
                           row[7] == "TRUE",
                           row[8],
                           row[9],
                           row[10],
                           row[11],
                           row[12],
                           row[13],
                           row[14] == "TRUE",
                           row[15],
                           int(row[17])])
