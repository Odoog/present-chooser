import hashlib
import logging
import os
import string
import random

from google_tables import SheetsClient


def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class Worker:

    def __init__(self, sheets_client: SheetsClient):
        self.sheets_client = sheets_client

    def generate_goods_files(self):
        file = open("site_worker/good.html", "r")
        good_block_code_original = file.read()
        for good in self.sheets_client.get_all_goods():

            good_block_code = good_block_code_original

            good_block_code = good_block_code\
                .replace("{src}", good.link)\
                .replace("{image-path}", good.photo_link)\
                .replace("{description}", good.name)\
                .replace("{price}", good.price_actual)\
                .replace("{store}", good.shop)
            with open('site_worker/goods/{}.txt'.format(good.ind), 'w', encoding="utf-8") as f:
                f.write(good_block_code)

    def build_site(self, good_ids):
        content = ""
        for ind in good_ids:
            with open('site_worker/goods/{}.txt'.format(ind), 'r', encoding="utf-8") as f:
                content += f.read()
        with open('site_worker/ex.html', 'r', encoding="utf-8") as f:
            site_blank = f.read().replace("{goods}", content)
        site_id = id_generator(size=4,
                               chars=string.ascii_lowercase)

        site_disk_source = "site_worker/sites/{}.html" if 'platform' in os.environ and os.environ['platform'] == "local" else "/var/www/html/symbol-gift.ru/{}.html".format(site_id)

        with open(site_disk_source.format(site_id), 'w', encoding="utf-8") as f:
            f.write(site_blank)
        logging.info("Build site with id {}".format(site_id))
        return "https://symbol-gift.ru/{}".format(site_id)
